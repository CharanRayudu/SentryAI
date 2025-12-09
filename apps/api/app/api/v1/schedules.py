from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter()

# --- Models ---

class ScheduleCreate(BaseModel):
    name: str
    target: str
    agent_id: str
    cron: str
    auto_pilot: bool = True
    enabled: bool = True

class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    target: Optional[str] = None
    cron: Optional[str] = None
    auto_pilot: Optional[bool] = None
    enabled: Optional[bool] = None

class Schedule(BaseModel):
    id: str
    name: str
    target: str
    agent_id: str
    cron: str
    cron_human: str
    auto_pilot: bool
    enabled: bool
    last_run: Optional[datetime] = None
    last_status: Optional[str] = None
    next_run: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

# --- In-Memory Store (Replace with PostgreSQL in production) ---
schedules_db: dict[str, Schedule] = {}

def cron_to_human(cron: str) -> str:
    """Convert cron expression to human-readable format"""
    presets = {
        "0 * * * *": "Every hour",
        "0 0 * * *": "Daily at midnight",
        "0 6 * * *": "Daily at 6:00 AM",
        "0 10 * * 1": "Every Monday at 10:00 AM",
        "0 0 1 * *": "Monthly on the 1st",
        "0 2 * * *": "Daily at 2:00 AM",
    }
    return presets.get(cron, f"Custom: {cron}")

# --- Routes ---

@router.get("/schedules", response_model=List[Schedule])
async def list_schedules():
    """List all scheduled missions"""
    return list(schedules_db.values())

@router.post("/schedules", response_model=Schedule)
async def create_schedule(schedule: ScheduleCreate):
    """Create a new scheduled mission"""
    schedule_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    new_schedule = Schedule(
        id=schedule_id,
        name=schedule.name,
        target=schedule.target,
        agent_id=schedule.agent_id,
        cron=schedule.cron,
        cron_human=cron_to_human(schedule.cron),
        auto_pilot=schedule.auto_pilot,
        enabled=schedule.enabled,
        created_at=now,
        updated_at=now
    )
    
    schedules_db[schedule_id] = new_schedule
    
    # TODO: Register with Temporal Schedules
    # temporal_client.create_schedule(
    #     schedule_id=schedule_id,
    #     schedule=Schedule(
    #         action=ScheduleActionStartWorkflow(
    #             "SecurityScanWorkflow",
    #             args=[schedule.target, "scheduled"],
    #             task_queue="sentry-scan-queue"
    #         ),
    #         spec=ScheduleSpec(cron_expressions=[schedule.cron])
    #     )
    # )
    
    return new_schedule

@router.get("/schedules/{schedule_id}", response_model=Schedule)
async def get_schedule(schedule_id: str):
    """Get a specific schedule"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedules_db[schedule_id]

@router.patch("/schedules/{schedule_id}", response_model=Schedule)
async def update_schedule(schedule_id: str, update: ScheduleUpdate):
    """Update a schedule"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    update_data = update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    if "cron" in update_data:
        schedule.cron_human = cron_to_human(update_data["cron"])
    
    schedule.updated_at = datetime.utcnow()
    schedules_db[schedule_id] = schedule
    
    # TODO: Update Temporal Schedule
    
    return schedule

@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Delete a schedule"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    del schedules_db[schedule_id]
    
    # TODO: Delete Temporal Schedule
    # temporal_client.get_schedule_handle(schedule_id).delete()
    
    return {"status": "deleted", "id": schedule_id}

@router.post("/schedules/{schedule_id}/trigger")
async def trigger_schedule(schedule_id: str):
    """Manually trigger a scheduled mission"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    
    # TODO: Trigger Temporal Workflow immediately
    # temporal_client.get_schedule_handle(schedule_id).trigger()
    
    return {"status": "triggered", "schedule": schedule.name}

@router.post("/schedules/{schedule_id}/pause")
async def pause_schedule(schedule_id: str):
    """Pause a schedule"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    schedule.enabled = False
    schedule.updated_at = datetime.utcnow()
    schedules_db[schedule_id] = schedule
    
    # TODO: Pause Temporal Schedule
    # temporal_client.get_schedule_handle(schedule_id).pause()
    
    return {"status": "paused", "schedule": schedule.name}

@router.post("/schedules/{schedule_id}/resume")
async def resume_schedule(schedule_id: str):
    """Resume a paused schedule"""
    if schedule_id not in schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule = schedules_db[schedule_id]
    schedule.enabled = True
    schedule.updated_at = datetime.utcnow()
    schedules_db[schedule_id] = schedule
    
    # TODO: Resume Temporal Schedule
    # temporal_client.get_schedule_handle(schedule_id).unpause()
    
    return {"status": "resumed", "schedule": schedule.name}

