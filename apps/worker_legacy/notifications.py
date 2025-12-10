import os
import json
import base64
import aiohttp
from temporalio import activity
from datetime import datetime
from typing import Optional, Literal

EventType = Literal[
    "scan_complete",
    "vulnerability_found", 
    "scan_failed",
    "high_severity_finding",
    "schedule_triggered"
]

@activity.defn
async def notify_integrations(
    event_type: EventType,
    payload: dict,
    platform: str = "slack"
) -> dict:
    """
    Sends a notification to external platforms (Slack, Discord, Jira, Linear).
    Enhanced to support rich formatting and multiple event types.
    """
    activity.logger.info(f"Dispatching {event_type} to {platform}")
    
    handlers = {
        "slack": send_slack_notification,
        "discord": send_discord_notification,
        "jira": create_jira_ticket,
        "linear": create_linear_issue,
        "webhook": send_webhook_notification
    }
    
    handler = handlers.get(platform)
    if not handler:
        activity.logger.warning(f"Unknown platform: {platform}")
        return {"status": "error", "reason": "unknown_platform"}
    
    try:
        result = await handler(event_type, payload)
        return result
    except Exception as e:
        activity.logger.error(f"Notification failed: {e}")
        return {"status": "error", "error": str(e)}


async def send_slack_notification(event_type: EventType, payload: dict) -> dict:
    """Send rich Slack notification with blocks"""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return {"status": "skipped", "reason": "no_config"}
    
    # Build Slack message blocks
    blocks = build_slack_blocks(event_type, payload)
    
    async with aiohttp.ClientSession() as session:
        slack_payload = {
            "text": get_fallback_text(event_type, payload),
            "blocks": blocks
        }
        
        async with session.post(webhook_url, json=slack_payload) as resp:
            if resp.status >= 400:
                return {"status": "error", "code": resp.status}
            return {"status": "sent", "platform": "slack"}


async def send_discord_notification(event_type: EventType, payload: dict) -> dict:
    """Send rich Discord notification with embeds"""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return {"status": "skipped", "reason": "no_config"}
    
    embed = build_discord_embed(event_type, payload)
    
    async with aiohttp.ClientSession() as session:
        discord_payload = {
            "content": get_fallback_text(event_type, payload),
            "embeds": [embed]
        }
        
        async with session.post(webhook_url, json=discord_payload) as resp:
            if resp.status >= 400:
                return {"status": "error", "code": resp.status}
            return {"status": "sent", "platform": "discord"}


async def create_jira_ticket(event_type: EventType, payload: dict) -> dict:
    """Create a Jira ticket for security findings"""
    base_url = os.getenv("JIRA_BASE_URL")
    email = os.getenv("JIRA_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")
    project_key = os.getenv("JIRA_PROJECT_KEY", "SEC")
    
    if not all([base_url, email, api_token]):
        return {"status": "skipped", "reason": "no_config"}
    
    # Build Jira ticket
    ticket = build_jira_ticket(event_type, payload, project_key)
    
    auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/rest/api/3/issue",
            json=ticket,
            headers=headers
        ) as resp:
            if resp.status >= 400:
                error_text = await resp.text()
                return {"status": "error", "code": resp.status, "message": error_text}
            
            data = await resp.json()
            return {
                "status": "created",
                "platform": "jira",
                "issue_key": data.get("key"),
                "issue_url": f"{base_url}/browse/{data.get('key')}"
            }


async def create_linear_issue(event_type: EventType, payload: dict) -> dict:
    """Create a Linear issue for security findings"""
    api_key = os.getenv("LINEAR_API_KEY")
    team_id = os.getenv("LINEAR_TEAM_ID")
    
    if not all([api_key, team_id]):
        return {"status": "skipped", "reason": "no_config"}
    
    # Build Linear issue
    title, description = build_linear_issue(event_type, payload)
    
    # Priority mapping
    priority_map = {
        "high_severity_finding": 1,  # Urgent
        "vulnerability_found": 2,     # High
        "scan_failed": 3,             # Medium
        "scan_complete": 4            # Low
    }
    
    mutation = """
    mutation CreateIssue($input: IssueCreateInput!) {
        issueCreate(input: $input) {
            success
            issue {
                id
                identifier
                url
            }
        }
    }
    """
    
    variables = {
        "input": {
            "teamId": team_id,
            "title": title,
            "description": description,
            "priority": priority_map.get(event_type, 3)
        }
    }
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.linear.app/graphql",
            json={"query": mutation, "variables": variables},
            headers=headers
        ) as resp:
            if resp.status >= 400:
                return {"status": "error", "code": resp.status}
            
            data = await resp.json()
            issue_data = data.get("data", {}).get("issueCreate", {}).get("issue", {})
            
            if issue_data:
                return {
                    "status": "created",
                    "platform": "linear",
                    "issue_id": issue_data.get("identifier"),
                    "issue_url": issue_data.get("url")
                }
            
            return {"status": "error", "message": "Failed to create issue"}


async def send_webhook_notification(event_type: EventType, payload: dict) -> dict:
    """Send generic webhook notification"""
    webhook_url = os.getenv("CUSTOM_WEBHOOK_URL")
    webhook_secret = os.getenv("CUSTOM_WEBHOOK_SECRET")
    
    if not webhook_url:
        return {"status": "skipped", "reason": "no_config"}
    
    webhook_payload = {
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "sentryai",
        "payload": payload
    }
    
    headers = {"Content-Type": "application/json"}
    if webhook_secret:
        import hmac
        import hashlib
        signature = hmac.new(
            webhook_secret.encode(),
            json.dumps(webhook_payload).encode(),
            hashlib.sha256
        ).hexdigest()
        headers["X-Sentry-Signature"] = signature
    
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=webhook_payload, headers=headers) as resp:
            if resp.status >= 400:
                return {"status": "error", "code": resp.status}
            return {"status": "sent", "platform": "webhook"}


# --- Message Builders ---

def get_fallback_text(event_type: EventType, payload: dict) -> str:
    """Generate plain text fallback"""
    templates = {
        "scan_complete": "✅ SentryAI: Scan completed for {target}. Found {findings_count} findings.",
        "vulnerability_found": "🚨 SentryAI: Vulnerability found - {title} on {target}",
        "scan_failed": "❌ SentryAI: Scan failed for {target}",
        "high_severity_finding": "🔴 SentryAI ALERT: High severity finding - {title} on {target}",
        "schedule_triggered": "⏰ SentryAI: Scheduled scan started for {target}"
    }
    
    template = templates.get(event_type, f"SentryAI Event: {event_type}")
    return template.format(**payload)


def build_slack_blocks(event_type: EventType, payload: dict) -> list:
    """Build rich Slack blocks"""
    
    color_map = {
        "scan_complete": "#10B981",
        "vulnerability_found": "#F59E0B",
        "scan_failed": "#EF4444",
        "high_severity_finding": "#EF4444",
        "schedule_triggered": "#7C3AED"
    }
    
    icon_map = {
        "scan_complete": "✅",
        "vulnerability_found": "🚨",
        "scan_failed": "❌",
        "high_severity_finding": "🔴",
        "schedule_triggered": "⏰"
    }
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{icon_map.get(event_type, '📋')} SentryAI Alert"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": get_fallback_text(event_type, payload)
            }
        }
    ]
    
    # Add target info
    if payload.get("target"):
        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Target:*\n{payload['target']}"},
                {"type": "mrkdwn", "text": f"*Time:*\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"}
            ]
        })
    
    # Add vulnerability details if present
    if event_type in ["vulnerability_found", "high_severity_finding"]:
        if payload.get("severity"):
            blocks.append({
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Severity:*\n{payload['severity']}"},
                    {"type": "mrkdwn", "text": f"*Tool:*\n{payload.get('tool', 'N/A')}"}
                ]
            })
    
    # Add action buttons
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "View in SentryAI"},
                "url": f"http://localhost:3000/operations/{payload.get('scan_id', '')}"
            }
        ]
    })
    
    return blocks


def build_discord_embed(event_type: EventType, payload: dict) -> dict:
    """Build Discord embed"""
    
    color_map = {
        "scan_complete": 0x10B981,
        "vulnerability_found": 0xF59E0B,
        "scan_failed": 0xEF4444,
        "high_severity_finding": 0xEF4444,
        "schedule_triggered": 0x7C3AED
    }
    
    embed = {
        "title": event_type.replace("_", " ").title(),
        "description": get_fallback_text(event_type, payload),
        "color": color_map.get(event_type, 0x7C3AED),
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {"text": "SentryAI Security Platform"}
    }
    
    fields = []
    if payload.get("target"):
        fields.append({"name": "Target", "value": payload["target"], "inline": True})
    if payload.get("severity"):
        fields.append({"name": "Severity", "value": payload["severity"], "inline": True})
    if payload.get("tool"):
        fields.append({"name": "Tool", "value": payload["tool"], "inline": True})
    
    if fields:
        embed["fields"] = fields
    
    return embed


def build_jira_ticket(event_type: EventType, payload: dict, project_key: str) -> dict:
    """Build Jira ticket payload"""
    
    # Issue type mapping
    issue_type = "Bug" if event_type in ["vulnerability_found", "high_severity_finding"] else "Task"
    
    # Priority mapping
    priority_map = {
        "high_severity_finding": "Highest",
        "vulnerability_found": "High",
        "scan_failed": "Medium",
        "scan_complete": "Low"
    }
    
    description = f"""
h2. SentryAI Security Finding

*Event Type:* {event_type.replace('_', ' ').title()}
*Target:* {payload.get('target', 'N/A')}
*Detected At:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

h3. Details
{payload.get('description', 'No additional details available.')}

h3. Remediation
{payload.get('remediation', 'Review the finding and take appropriate action.')}

----
_This ticket was automatically created by SentryAI._
    """
    
    return {
        "fields": {
            "project": {"key": project_key},
            "summary": f"[SentryAI] {payload.get('title', event_type.replace('_', ' ').title())}",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            },
            "issuetype": {"name": issue_type},
            "priority": {"name": priority_map.get(event_type, "Medium")},
            "labels": ["sentryai", "security", event_type]
        }
    }


def build_linear_issue(event_type: EventType, payload: dict) -> tuple[str, str]:
    """Build Linear issue title and description"""
    
    title = f"[SentryAI] {payload.get('title', event_type.replace('_', ' ').title())}"
    
    description = f"""
## SentryAI Security Finding

**Event Type:** {event_type.replace('_', ' ').title()}
**Target:** {payload.get('target', 'N/A')}
**Detected At:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

### Details
{payload.get('description', 'No additional details available.')}

### Remediation
{payload.get('remediation', 'Review the finding and take appropriate action.')}

---
*This issue was automatically created by SentryAI.*
    """
    
    return title, description
