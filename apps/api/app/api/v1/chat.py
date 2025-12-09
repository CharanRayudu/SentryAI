"""
WebSocket Chat Endpoint for Mission Control
Handles real-time communication between frontend and AI agent
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.events import manager
from app.core.security import command_validator, input_validator
import json
import uuid
import asyncio

router = APIRouter()


@router.websocket("/ws/mission")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str = Query(None)
):
    """
    WebSocket endpoint for Mission Control.
    
    Message Types (Client -> Server):
    - client:message - User sends a chat message
    - client:confirm_plan - User confirms/modifies execution plan
    - client:cancel_job - Cancel a running job
    - client:subscribe_logs - Subscribe to job log stream
    - client:unsubscribe_logs - Unsubscribe from job log stream
    
    Message Types (Server -> Client):
    - server:agent_thought - AI thinking/processing step
    - server:plan_proposal - Proposed execution plan for approval
    - server:job_log - Real-time log entry from a job
    - server:job_status - Job status update
    - server:graph_update - Graph topology change
    - server:error - Error message
    """
    # Accept connection
    session_id = await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            try:
                payload = json.loads(data)
                message_type = payload.get("type", "")
                
                # Route message by type
                if message_type == "client:message":
                    await handle_user_message(session_id, payload)
                
                elif message_type == "client:confirm_plan":
                    await handle_plan_confirmation(session_id, payload)
                
                elif message_type == "client:cancel_job":
                    await handle_job_cancel(session_id, payload)
                
                elif message_type == "client:subscribe_logs":
                    job_id = payload.get("job_id")
                    if job_id:
                        manager.subscribe_session(session_id, f"job_logs:{job_id}")
                        await manager.send_to_session(session_id, {
                            "type": "server:subscribed",
                            "channel": f"job_logs:{job_id}"
                        })
                
                elif message_type == "client:unsubscribe_logs":
                    job_id = payload.get("job_id")
                    if job_id:
                        manager.unsubscribe_session(session_id, f"job_logs:{job_id}")
                        await manager.send_to_session(session_id, {
                            "type": "server:unsubscribed",
                            "channel": f"job_logs:{job_id}"
                        })
                
                else:
                    await manager.send_to_session(session_id, {
                        "type": "server:error",
                        "message": f"Unknown message type: {message_type}"
                    })
                    
            except json.JSONDecodeError:
                await manager.send_to_session(session_id, {
                    "type": "server:error",
                    "message": "Invalid JSON payload"
                })
            except Exception as e:
                await manager.send_to_session(session_id, {
                    "type": "server:error",
                    "message": f"Error processing message: {str(e)}"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)


async def handle_user_message(session_id: str, payload: dict):
    """
    Handle incoming user message.
    This triggers the AI planning process.
    """
    user_content = payload.get("content", "")
    context_files = payload.get("context_files", [])
    
    if not user_content.strip():
        await manager.send_to_session(session_id, {
            "type": "server:error",
            "message": "Message content cannot be empty"
        })
        return
    
    # Step 1: Acknowledge receipt
    await manager.send_to_session(session_id, {
        "type": "server:agent_thought",
        "step": "Parsing Intent",
        "log": f"Received mission objective: {user_content[:100]}...",
        "status": "processing"
    })
    
    # Step 2: Simulate context retrieval
    await asyncio.sleep(0.8)
    await manager.send_to_session(session_id, {
        "type": "server:agent_thought",
        "step": "Context Retrieval",
        "log": f"Querying knowledge base... ({len(context_files)} context files)",
        "status": "processing"
    })
    
    # Step 3: Simulate planning
    await asyncio.sleep(1.0)
    await manager.send_to_session(session_id, {
        "type": "server:agent_thought",
        "step": "Strategic Planning",
        "log": "Analyzing target scope and selecting appropriate tools...",
        "status": "processing"
    })
    
    # Step 4: Extract target from message (simple heuristic)
    target = extract_target(user_content)
    
    # Step 5: Generate plan based on intent
    await asyncio.sleep(0.8)
    plan_id = str(uuid.uuid4())
    plan_steps = generate_plan(user_content, target)
    
    # Step 6: Propose plan
    await manager.send_to_session(session_id, {
        "type": "server:plan_proposal",
        "plan_id": plan_id,
        "intent": extract_intent(user_content),
        "target": target,
        "steps": plan_steps
    })


async def handle_plan_confirmation(session_id: str, payload: dict):
    """
    Handle plan confirmation from user.
    This triggers the actual execution.
    """
    plan_id = payload.get("plan_id")
    approved_steps = payload.get("approved_steps", [])
    
    if not plan_id:
        await manager.send_to_session(session_id, {
            "type": "server:error",
            "message": "Plan ID is required"
        })
        return
    
    # Acknowledge confirmation
    await manager.send_to_session(session_id, {
        "type": "server:agent_thought",
        "step": "Execution",
        "log": f"Mission confirmed. Dispatching {len(approved_steps)} tasks...",
        "status": "processing"
    })
    
    # TODO: In production, this would:
    # 1. Start a Temporal workflow with the approved steps
    # 2. Return the job_id for tracking
    # 3. The workflow would publish logs via Redis
    
    job_id = str(uuid.uuid4())
    
    await asyncio.sleep(0.5)
    await manager.send_to_session(session_id, {
        "type": "server:job_status",
        "job_id": job_id,
        "status": "running",
        "message": "Mission initiated successfully"
    })


async def handle_job_cancel(session_id: str, payload: dict):
    """Handle job cancellation request"""
    job_id = payload.get("job_id")
    
    if not job_id:
        await manager.send_to_session(session_id, {
            "type": "server:error",
            "message": "Job ID is required"
        })
        return
    
    # TODO: In production, call temporal_service.cancel_workflow(job_id)
    
    await manager.send_to_session(session_id, {
        "type": "server:job_status",
        "job_id": job_id,
        "status": "cancelled",
        "message": "Job cancelled by user"
    })


# --- Helper Functions ---

def extract_target(message: str) -> str:
    """Extract target (domain/IP) from user message"""
    import re
    
    # Look for domain patterns
    domain_pattern = r'([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z]{2,}'
    domains = re.findall(domain_pattern, message)
    if domains:
        return domains[0].rstrip('.')
    
    # Look for IP patterns
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ips = re.findall(ip_pattern, message)
    if ips:
        return ips[0]
    
    # Default
    return "target.example.com"


def extract_intent(message: str) -> str:
    """Extract high-level intent from user message"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["xss", "cross-site", "script"]):
        return "XSS Vulnerability Audit"
    elif any(word in message_lower for word in ["sql", "injection", "sqli"]):
        return "SQL Injection Audit"
    elif any(word in message_lower for word in ["recon", "enumerate", "discover", "subdomain"]):
        return "Reconnaissance & Discovery"
    elif any(word in message_lower for word in ["port", "service", "scan"]):
        return "Port Scanning & Service Detection"
    elif any(word in message_lower for word in ["full", "comprehensive", "complete"]):
        return "Comprehensive Security Audit"
    elif any(word in message_lower for word in ["api", "endpoint", "rest"]):
        return "API Security Assessment"
    else:
        return "Security Assessment"


def generate_plan(message: str, target: str) -> list:
    """Generate execution plan based on user intent"""
    message_lower = message.lower()
    steps = []
    step_id = 1
    
    # Reconnaissance steps
    if any(word in message_lower for word in ["recon", "discover", "full", "comprehensive", "scan"]):
        steps.append({
            "id": step_id,
            "title": f"Subdomain Enumeration for {target}",
            "tool": "subfinder",
            "args": f"-d {target} -silent",
            "enabled": True
        })
        step_id += 1
        
        steps.append({
            "id": step_id,
            "title": "Port Scanning",
            "tool": "naabu",
            "args": f"-host {target} -top-ports 1000",
            "enabled": True
        })
        step_id += 1
    
    # XSS-specific
    if any(word in message_lower for word in ["xss", "cross-site", "script"]):
        steps.append({
            "id": step_id,
            "title": "XSS Vulnerability Scan",
            "tool": "nuclei",
            "args": f"-u {target} -tags xss",
            "enabled": True
        })
        step_id += 1
    
    # SQL Injection
    if any(word in message_lower for word in ["sql", "injection", "sqli"]):
        steps.append({
            "id": step_id,
            "title": "SQL Injection Scan",
            "tool": "nuclei",
            "args": f"-u {target} -tags sqli",
            "enabled": True
        })
        step_id += 1
    
    # General vulnerability scan
    if any(word in message_lower for word in ["vuln", "vulnerability", "full", "comprehensive"]) or len(steps) == 0:
        steps.append({
            "id": step_id,
            "title": "Vulnerability Assessment",
            "tool": "nuclei",
            "args": f"-u {target} -severity medium,high,critical",
            "enabled": True
        })
        step_id += 1
    
    # Technology detection
    if any(word in message_lower for word in ["tech", "stack", "detect", "fingerprint"]):
        steps.append({
            "id": step_id,
            "title": "Technology Fingerprinting",
            "tool": "httpx",
            "args": f"-u {target} -tech-detect",
            "enabled": True
        })
        step_id += 1
    
    # Default minimal plan if nothing matched
    if len(steps) == 0:
        steps = [
            {"id": 1, "title": "Subdomain Discovery", "tool": "subfinder", "args": f"-d {target}", "enabled": True},
            {"id": 2, "title": "Port Scan", "tool": "naabu", "args": f"-host {target}", "enabled": True},
            {"id": 3, "title": "Vulnerability Scan", "tool": "nuclei", "args": f"-u {target}", "enabled": True},
        ]
    
    return steps
