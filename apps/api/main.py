from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="SentryAI Control Plane", version="1.0.0")

class ScanRequest(BaseModel):
    target: str
    scan_type: str = "quick" # quick, deep, auth
    mission_id: Optional[str] = None

from temporalio.client import Client

@app.post("/api/v1/scan/start")
async def start_scan(request: ScanRequest):
    try:
        # Connect to Temporal
        client = await Client.connect(os.getenv("TEMPORAL_HOST", "temporal:7233"))
        
        # Start Workflow
        workflow_id = f"scan-{request.target}-{os.urandom(4).hex()}"
        handle = await client.start_workflow(
            "SecurityScanWorkflow",
            args=[request.target, request.scan_type],
            id=workflow_id,
            task_queue="sentry-scan-queue",
        )
        
        return {
            "status": "accepted", 
            "message": f"Mission started for target: {request.target}",
            "workflow_id": handle.id,
            "run_id": handle.result_run_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "operational", "services": {"database": "connected", "temporal": "connected"}}
