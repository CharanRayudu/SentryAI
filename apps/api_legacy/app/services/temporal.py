"""
Temporal Client Wrapper
Handles workflow management, scheduling, and job control
"""
import os
import asyncio
from typing import Optional, Dict, Any, List
from datetime import timedelta
from temporalio.client import Client, WorkflowHandle
from temporalio.common import WorkflowIDReusePolicy

# Workflow names (must match worker definitions)
SECURITY_SCAN_WORKFLOW = "SecurityScanWorkflow"
INGEST_DOCUMENT_WORKFLOW = "IngestDocumentWorkflow"
TOOL_INSTALL_WORKFLOW = "ToolInstallWorkflow"

# Task queues
SCAN_QUEUE = "sentry-scan-queue"
INGEST_QUEUE = "sentry-ingest-queue"


class TemporalService:
    """Wrapper for Temporal client operations"""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._host = os.getenv("TEMPORAL_HOST", "temporal:7233")
    
    async def connect(self) -> Client:
        """Get or create Temporal client connection"""
        if self._client is None:
            self._client = await Client.connect(self._host)
        return self._client
    
    async def disconnect(self):
        """Close client connection"""
        if self._client:
            # Temporal Python SDK doesn't have explicit close
            self._client = None

    # --- Workflow Operations ---
    
    async def start_scan_workflow(
        self,
        target: str,
        scan_type: str,
        config: Dict[str, Any],
        workflow_id: Optional[str] = None,
        auto_pilot: bool = False
    ) -> str:
        """Start a security scan workflow"""
        client = await self.connect()
        
        workflow_id = workflow_id or f"scan-{target}-{int(asyncio.get_event_loop().time())}"
        
        handle = await client.start_workflow(
            SECURITY_SCAN_WORKFLOW,
            args=[target, scan_type, config, auto_pilot],
            id=workflow_id,
            task_queue=SCAN_QUEUE,
            id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY,
            execution_timeout=timedelta(hours=24),  # Max scan duration
        )
        
        return handle.id
    
    async def start_ingest_workflow(
        self,
        document_id: str,
        file_path: str,
        file_type: str,
        project_id: str
    ) -> str:
        """Start a document ingestion workflow"""
        client = await self.connect()
        
        workflow_id = f"ingest-{document_id}"
        
        handle = await client.start_workflow(
            INGEST_DOCUMENT_WORKFLOW,
            args=[document_id, file_path, file_type, project_id],
            id=workflow_id,
            task_queue=INGEST_QUEUE,
            execution_timeout=timedelta(hours=1),
        )
        
        return handle.id
    
    async def start_tool_install_workflow(
        self,
        tool_name: str,
        github_url: str
    ) -> str:
        """Start a tool installation workflow"""
        client = await self.connect()
        
        workflow_id = f"install-{tool_name}-{int(asyncio.get_event_loop().time())}"
        
        handle = await client.start_workflow(
            TOOL_INSTALL_WORKFLOW,
            args=[tool_name, github_url],
            id=workflow_id,
            task_queue=SCAN_QUEUE,
            execution_timeout=timedelta(minutes=30),
        )
        
        return handle_id

    # --- Job Control ---
    
    async def get_workflow_handle(self, workflow_id: str) -> WorkflowHandle:
        """Get handle to an existing workflow"""
        client = await self.connect()
        return client.get_workflow_handle(workflow_id)
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution status"""
        try:
            handle = await self.get_workflow_handle(workflow_id)
            desc = await handle.describe()
            
            return {
                "id": workflow_id,
                "status": desc.status.name,
                "start_time": desc.start_time.isoformat() if desc.start_time else None,
                "close_time": desc.close_time.isoformat() if desc.close_time else None,
                "execution_time": desc.execution_time.total_seconds() if desc.execution_time else None,
            }
        except Exception as e:
            return {
                "id": workflow_id,
                "status": "UNKNOWN",
                "error": str(e)
            }
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        try:
            handle = await self.get_workflow_handle(workflow_id)
            await handle.cancel()
            return True
        except Exception as e:
            print(f"Failed to cancel workflow {workflow_id}: {e}")
            return False
    
    async def terminate_workflow(self, workflow_id: str, reason: str = "User requested") -> bool:
        """Forcefully terminate a workflow"""
        try:
            handle = await self.get_workflow_handle(workflow_id)
            await handle.terminate(reason=reason)
            return True
        except Exception as e:
            print(f"Failed to terminate workflow {workflow_id}: {e}")
            return False
    
    async def signal_workflow(self, workflow_id: str, signal_name: str, data: Any = None) -> bool:
        """Send a signal to a workflow"""
        try:
            handle = await self.get_workflow_handle(workflow_id)
            await handle.signal(signal_name, data)
            return True
        except Exception as e:
            print(f"Failed to signal workflow {workflow_id}: {e}")
            return False

    # --- Schedule Operations ---
    
    async def create_schedule(
        self,
        schedule_id: str,
        workflow_name: str,
        workflow_args: List[Any],
        cron_expression: str,
        task_queue: str = SCAN_QUEUE
    ) -> str:
        """Create a scheduled workflow"""
        client = await self.connect()
        
        # Note: Temporal Schedule API requires specific imports
        # This is a simplified version
        from temporalio.client import (
            Schedule,
            ScheduleSpec,
            ScheduleActionStartWorkflow,
            ScheduleState,
        )
        
        await client.create_schedule(
            schedule_id,
            Schedule(
                action=ScheduleActionStartWorkflow(
                    workflow_name,
                    args=workflow_args,
                    id=f"{schedule_id}-{{{{.ScheduledTime}}}}",
                    task_queue=task_queue,
                ),
                spec=ScheduleSpec(
                    cron_expressions=[cron_expression],
                ),
                state=ScheduleState(
                    paused=False,
                ),
            ),
        )
        
        return schedule_id
    
    async def pause_schedule(self, schedule_id: str) -> bool:
        """Pause a schedule"""
        try:
            client = await self.connect()
            handle = client.get_schedule_handle(schedule_id)
            await handle.pause()
            return True
        except Exception as e:
            print(f"Failed to pause schedule {schedule_id}: {e}")
            return False
    
    async def resume_schedule(self, schedule_id: str) -> bool:
        """Resume a paused schedule"""
        try:
            client = await self.connect()
            handle = client.get_schedule_handle(schedule_id)
            await handle.unpause()
            return True
        except Exception as e:
            print(f"Failed to resume schedule {schedule_id}: {e}")
            return False
    
    async def trigger_schedule(self, schedule_id: str) -> bool:
        """Manually trigger a scheduled workflow"""
        try:
            client = await self.connect()
            handle = client.get_schedule_handle(schedule_id)
            await handle.trigger()
            return True
        except Exception as e:
            print(f"Failed to trigger schedule {schedule_id}: {e}")
            return False
    
    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule"""
        try:
            client = await self.connect()
            handle = client.get_schedule_handle(schedule_id)
            await handle.delete()
            return True
        except Exception as e:
            print(f"Failed to delete schedule {schedule_id}: {e}")
            return False


# Singleton instance
temporal_service = TemporalService()

