"""
Missions API Routes
Job/scan control and workflow management
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.services.temporal import temporal_service
from app.core.security import command_validator, input_validator, raise_security_violation

router = APIRouter()


# --- Request/Response Models ---

class MissionCreate(BaseModel):
    target: str
    scan_type: str = "full"  # full, recon, vuln, custom
    config: Optional[Dict[str, Any]] = None
    auto_pilot: bool = False
    tasks: Optional[List[str]] = None  # Specific tasks to run


class MissionResponse(BaseModel):
    id: str
    workflow_id: str
    target: str
    scan_type: str
    status: str
    created_at: datetime


class MissionStatus(BaseModel):
    id: str
    status: str
    start_time: Optional[str] = None
    close_time: Optional[str] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None


class MissionSignal(BaseModel):
    signal_name: str
    data: Optional[Any] = None


# --- In-Memory Store (Replace with DB in production) ---
missions_db: Dict[str, Dict] = {}


# --- Routes ---

@router.post("/missions", response_model=MissionResponse)
async def create_mission(mission: MissionCreate, background_tasks: BackgroundTasks):
    """
    Create and start a new security mission.
    Triggers a Temporal workflow for execution.
    """
    # Validate target
    is_valid, error = input_validator.validate_target(mission.target)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Generate IDs
    mission_id = str(uuid.uuid4())
    workflow_id = f"mission-{mission_id}"
    
    try:
        # Build config
        config = mission.config or {}
        if mission.tasks:
            config["tasks"] = mission.tasks
        
        # Start Temporal workflow
        await temporal_service.start_scan_workflow(
            target=mission.target,
            scan_type=mission.scan_type,
            config=config,
            workflow_id=workflow_id,
            auto_pilot=mission.auto_pilot
        )
        
        # Store mission info
        now = datetime.utcnow()
        missions_db[mission_id] = {
            "id": mission_id,
            "workflow_id": workflow_id,
            "target": mission.target,
            "scan_type": mission.scan_type,
            "config": config,
            "auto_pilot": mission.auto_pilot,
            "status": "running",
            "created_at": now,
        }
        
        return MissionResponse(
            id=mission_id,
            workflow_id=workflow_id,
            target=mission.target,
            scan_type=mission.scan_type,
            status="running",
            created_at=now
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start mission: {str(e)}")


@router.get("/missions", response_model=List[MissionResponse])
async def list_missions(
    status: Optional[str] = None,
    limit: int = 50
):
    """List all missions, optionally filtered by status"""
    missions = list(missions_db.values())
    
    if status:
        missions = [m for m in missions if m.get("status") == status]
    
    # Sort by created_at descending
    missions.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    
    return [
        MissionResponse(
            id=m["id"],
            workflow_id=m["workflow_id"],
            target=m["target"],
            scan_type=m["scan_type"],
            status=m["status"],
            created_at=m["created_at"]
        )
        for m in missions[:limit]
    ]


@router.get("/missions/{mission_id}", response_model=MissionStatus)
async def get_mission_status(mission_id: str):
    """Get detailed status of a mission"""
    if mission_id not in missions_db:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    mission = missions_db[mission_id]
    
    try:
        # Get workflow status from Temporal
        workflow_status = await temporal_service.get_workflow_status(mission["workflow_id"])
        
        # Update local status
        temporal_status_map = {
            "RUNNING": "running",
            "COMPLETED": "completed",
            "FAILED": "failed",
            "CANCELED": "cancelled",
            "TERMINATED": "terminated",
        }
        mission["status"] = temporal_status_map.get(workflow_status.get("status"), mission["status"])
        
        return MissionStatus(
            id=mission_id,
            status=mission["status"],
            start_time=workflow_status.get("start_time"),
            close_time=workflow_status.get("close_time"),
            execution_time=workflow_status.get("execution_time"),
            error=workflow_status.get("error")
        )
        
    except Exception as e:
        return MissionStatus(
            id=mission_id,
            status=mission.get("status", "unknown"),
            error=str(e)
        )


@router.post("/missions/{mission_id}/cancel")
async def cancel_mission(mission_id: str):
    """Cancel a running mission"""
    if mission_id not in missions_db:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    mission = missions_db[mission_id]
    
    try:
        success = await temporal_service.cancel_workflow(mission["workflow_id"])
        
        if success:
            mission["status"] = "cancelled"
            return {"status": "cancelled", "mission_id": mission_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to cancel mission")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cancel failed: {str(e)}")


@router.post("/missions/{mission_id}/terminate")
async def terminate_mission(mission_id: str, reason: str = "User requested"):
    """Forcefully terminate a mission"""
    if mission_id not in missions_db:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    mission = missions_db[mission_id]
    
    try:
        success = await temporal_service.terminate_workflow(mission["workflow_id"], reason)
        
        if success:
            mission["status"] = "terminated"
            return {"status": "terminated", "mission_id": mission_id, "reason": reason}
        else:
            raise HTTPException(status_code=500, detail="Failed to terminate mission")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terminate failed: {str(e)}")


@router.post("/missions/{mission_id}/signal")
async def signal_mission(mission_id: str, signal: MissionSignal):
    """Send a signal to a running mission workflow"""
    if mission_id not in missions_db:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    mission = missions_db[mission_id]
    
    try:
        success = await temporal_service.signal_workflow(
            mission["workflow_id"],
            signal.signal_name,
            signal.data
        )
        
        if success:
            return {"status": "signaled", "signal": signal.signal_name}
        else:
            raise HTTPException(status_code=500, detail="Failed to send signal")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signal failed: {str(e)}")


@router.delete("/missions/{mission_id}")
async def delete_mission(mission_id: str):
    """Delete a mission record (does not affect running workflow)"""
    if mission_id not in missions_db:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    del missions_db[mission_id]
    return {"status": "deleted", "mission_id": mission_id}


# --- Scan Start Endpoint (for backward compatibility) ---

@router.post("/scan/start")
async def start_scan(
    target: str,
    scan_type: str = "custom",
    tasks: Optional[List[str]] = None,
    auto_pilot: bool = False
):
    """
    Legacy endpoint to start a scan.
    Creates a mission under the hood.
    """
    mission = MissionCreate(
        target=target,
        scan_type=scan_type,
        tasks=tasks,
        auto_pilot=auto_pilot
    )
    
    # Reuse the create_mission logic
    return await create_mission(mission, BackgroundTasks())

