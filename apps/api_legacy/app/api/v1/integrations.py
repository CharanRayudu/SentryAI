from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime
import uuid
import aiohttp
import os

router = APIRouter()

# --- Models ---

IntegrationType = Literal["slack", "jira", "linear", "discord", "webhook"]
EventType = Literal["scan_complete", "vulnerability_found", "scan_failed", "high_severity_finding", "schedule_triggered"]

class IntegrationCreate(BaseModel):
    type: IntegrationType
    name: str
    config: dict
    events: List[EventType]
    enabled: bool = True

class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[dict] = None
    events: Optional[List[EventType]] = None
    enabled: Optional[bool] = None

class Integration(BaseModel):
    id: str
    type: IntegrationType
    name: str
    config: dict  # Sensitive fields will be masked
    events: List[EventType]
    enabled: bool
    last_used: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class IntegrationTestResult(BaseModel):
    success: bool
    message: str
    latency_ms: Optional[int] = None

# --- In-Memory Store (Replace with PostgreSQL in production) ---
integrations_db: dict[str, dict] = {}

def mask_config(config: dict) -> dict:
    """Mask sensitive fields in config"""
    masked = {}
    sensitive_keys = ["api_token", "api_key", "secret", "password", "webhook_url"]
    for key, value in config.items():
        if any(s in key.lower() for s in sensitive_keys) and value:
            masked[key] = value[:8] + "..." + value[-4:] if len(value) > 12 else "****"
        else:
            masked[key] = value
    return masked

# --- Routes ---

@router.get("/integrations", response_model=List[Integration])
async def list_integrations():
    """List all integrations"""
    result = []
    for data in integrations_db.values():
        integration = Integration(**data)
        integration.config = mask_config(integration.config)
        result.append(integration)
    return result

@router.post("/integrations", response_model=Integration)
async def create_integration(integration: IntegrationCreate):
    """Create a new integration"""
    integration_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    data = {
        "id": integration_id,
        "type": integration.type,
        "name": integration.name,
        "config": integration.config,
        "events": integration.events,
        "enabled": integration.enabled,
        "last_used": None,
        "created_at": now,
        "updated_at": now
    }
    
    integrations_db[integration_id] = data
    
    # Return with masked config
    response = Integration(**data)
    response.config = mask_config(response.config)
    return response

@router.get("/integrations/{integration_id}", response_model=Integration)
async def get_integration(integration_id: str):
    """Get a specific integration"""
    if integration_id not in integrations_db:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    data = integrations_db[integration_id]
    integration = Integration(**data)
    integration.config = mask_config(integration.config)
    return integration

@router.patch("/integrations/{integration_id}", response_model=Integration)
async def update_integration(integration_id: str, update: IntegrationUpdate):
    """Update an integration"""
    if integration_id not in integrations_db:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    data = integrations_db[integration_id]
    update_data = update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        data[field] = value
    
    data["updated_at"] = datetime.utcnow()
    integrations_db[integration_id] = data
    
    integration = Integration(**data)
    integration.config = mask_config(integration.config)
    return integration

@router.delete("/integrations/{integration_id}")
async def delete_integration(integration_id: str):
    """Delete an integration"""
    if integration_id not in integrations_db:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    del integrations_db[integration_id]
    return {"status": "deleted", "id": integration_id}

@router.post("/integrations/{integration_id}/test", response_model=IntegrationTestResult)
async def test_integration(integration_id: str):
    """Test an integration by sending a test message"""
    if integration_id not in integrations_db:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    data = integrations_db[integration_id]
    integration_type = data["type"]
    config = data["config"]
    
    import time
    start = time.time()
    
    try:
        async with aiohttp.ClientSession() as session:
            if integration_type == "slack":
                webhook_url = config.get("webhook_url")
                if not webhook_url:
                    return IntegrationTestResult(success=False, message="Missing webhook URL")
                
                payload = {
                    "text": "🔒 *SentryAI Test Message*\nThis is a test notification from SentryAI. If you see this, your Slack integration is working correctly!",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "🔒 *SentryAI Test Message*\n\nThis is a test notification from SentryAI. Your integration is configured correctly!"
                            }
                        }
                    ]
                }
                
                async with session.post(webhook_url, json=payload) as resp:
                    latency = int((time.time() - start) * 1000)
                    if resp.status == 200:
                        return IntegrationTestResult(success=True, message="Test message sent successfully", latency_ms=latency)
                    else:
                        return IntegrationTestResult(success=False, message=f"Slack returned status {resp.status}")
            
            elif integration_type == "discord":
                webhook_url = config.get("webhook_url")
                if not webhook_url:
                    return IntegrationTestResult(success=False, message="Missing webhook URL")
                
                payload = {
                    "content": "🔒 **SentryAI Test Message**\nThis is a test notification from SentryAI. If you see this, your Discord integration is working correctly!",
                    "embeds": [{
                        "title": "Integration Test",
                        "description": "Your SentryAI integration is configured correctly!",
                        "color": 8061183  # Purple
                    }]
                }
                
                async with session.post(webhook_url, json=payload) as resp:
                    latency = int((time.time() - start) * 1000)
                    if resp.status in [200, 204]:
                        return IntegrationTestResult(success=True, message="Test message sent successfully", latency_ms=latency)
                    else:
                        return IntegrationTestResult(success=False, message=f"Discord returned status {resp.status}")
            
            elif integration_type == "jira":
                base_url = config.get("base_url")
                email = config.get("email")
                api_token = config.get("api_token")
                
                if not all([base_url, email, api_token]):
                    return IntegrationTestResult(success=False, message="Missing Jira configuration")
                
                # Test by fetching user info
                import base64
                auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()
                headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
                
                async with session.get(f"{base_url}/rest/api/3/myself", headers=headers) as resp:
                    latency = int((time.time() - start) * 1000)
                    if resp.status == 200:
                        return IntegrationTestResult(success=True, message="Jira connection verified", latency_ms=latency)
                    else:
                        return IntegrationTestResult(success=False, message=f"Jira authentication failed (status {resp.status})")
            
            elif integration_type == "linear":
                api_key = config.get("api_key")
                if not api_key:
                    return IntegrationTestResult(success=False, message="Missing Linear API key")
                
                headers = {"Authorization": api_key, "Content-Type": "application/json"}
                query = {"query": "{ viewer { id name } }"}
                
                async with session.post("https://api.linear.app/graphql", json=query, headers=headers) as resp:
                    latency = int((time.time() - start) * 1000)
                    if resp.status == 200:
                        data = await resp.json()
                        if "data" in data and data["data"].get("viewer"):
                            return IntegrationTestResult(success=True, message="Linear connection verified", latency_ms=latency)
                    return IntegrationTestResult(success=False, message="Linear authentication failed")
            
            elif integration_type == "webhook":
                url = config.get("url")
                if not url:
                    return IntegrationTestResult(success=False, message="Missing webhook URL")
                
                payload = {
                    "type": "test",
                    "source": "sentryai",
                    "message": "Test notification from SentryAI",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                async with session.post(url, json=payload) as resp:
                    latency = int((time.time() - start) * 1000)
                    if resp.status < 400:
                        return IntegrationTestResult(success=True, message="Webhook test successful", latency_ms=latency)
                    else:
                        return IntegrationTestResult(success=False, message=f"Webhook returned status {resp.status}")
            
            return IntegrationTestResult(success=False, message=f"Unknown integration type: {integration_type}")
            
    except Exception as e:
        return IntegrationTestResult(success=False, message=f"Connection failed: {str(e)}")

# --- Event Dispatch ---

async def dispatch_event(event_type: EventType, payload: dict):
    """Dispatch an event to all enabled integrations that subscribe to it"""
    for integration_id, data in integrations_db.items():
        if not data["enabled"]:
            continue
        if event_type not in data["events"]:
            continue
        
        try:
            await send_notification(data, event_type, payload)
            data["last_used"] = datetime.utcnow()
            integrations_db[integration_id] = data
        except Exception as e:
            print(f"Failed to dispatch to {data['name']}: {e}")

async def send_notification(integration: dict, event_type: str, payload: dict):
    """Send notification to a specific integration"""
    integration_type = integration["type"]
    config = integration["config"]
    
    message = format_message(event_type, payload, integration_type)
    
    async with aiohttp.ClientSession() as session:
        if integration_type == "slack":
            webhook_url = config.get("webhook_url")
            await session.post(webhook_url, json={"text": message, "blocks": format_slack_blocks(event_type, payload)})
        
        elif integration_type == "discord":
            webhook_url = config.get("webhook_url")
            await session.post(webhook_url, json={"content": message, "embeds": format_discord_embeds(event_type, payload)})
        
        elif integration_type == "webhook":
            url = config.get("url")
            await session.post(url, json={"event": event_type, "payload": payload})

def format_message(event_type: str, payload: dict, platform: str) -> str:
    """Format event message for different platforms"""
    templates = {
        "scan_complete": "✅ Scan completed for {target}. Found {findings_count} findings.",
        "vulnerability_found": "🚨 Vulnerability found: {title} on {target}",
        "scan_failed": "❌ Scan failed for {target}: {error}",
        "high_severity_finding": "🔴 HIGH SEVERITY: {title} detected on {target}",
        "schedule_triggered": "⏰ Scheduled scan started for {target}"
    }
    
    template = templates.get(event_type, f"Event: {event_type}")
    return template.format(**payload)

def format_slack_blocks(event_type: str, payload: dict) -> list:
    """Format Slack blocks for rich messages"""
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": format_message(event_type, payload, "slack")
            }
        }
    ]

def format_discord_embeds(event_type: str, payload: dict) -> list:
    """Format Discord embeds for rich messages"""
    colors = {
        "scan_complete": 0x10B981,
        "vulnerability_found": 0xF59E0B,
        "scan_failed": 0xEF4444,
        "high_severity_finding": 0xEF4444,
        "schedule_triggered": 0x7C3AED
    }
    
    return [{
        "title": event_type.replace("_", " ").title(),
        "description": format_message(event_type, payload, "discord"),
        "color": colors.get(event_type, 0x7C3AED)
    }]

