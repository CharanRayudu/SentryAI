import os
from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker
from activities import run_tool_scan

@workflow.defn
class SecurityScanWorkflow:
    @workflow.run
    async def run(self, target: str, scan_type: str) -> dict:
        workflow.logger.info(f"Starting scan workflow for {target}")
        
        # Phase 1: Simple linear execution (Plan -> Act)
        # In Phase 2: This becomes a Loop with LangGraph
        
        # Step 1: Subdomain Enumeration (Mocked or Real)
        discovery_result = await workflow.execute_activity(
            run_tool_scan,
            {"tool": "subfinder", "target": target, "args": "-silent"},
            start_to_close_timeout_seconds=300
        )
        
        # Step 2: Port Scan (if discovery found something)
        # For MVP, just return the discovery result
        return {
            "status": "completed",
            "target": target,
            "findings": discovery_result
        }

async def main():
    client = await Client.connect(os.getenv("TEMPORAL_HOST", "temporal:7233"))
    
    worker = Worker(
        client,
        task_queue="sentry-scan-queue",
        workflows=[SecurityScanWorkflow],
        activities=[run_tool_scan],
    )
    print("Worker started, listening on 'sentry-scan-queue'...")
    await worker.run()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
