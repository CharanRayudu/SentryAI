"""
Event Management & WebSocket Connection Manager
Handles real-time communication between frontend, API, and workers
"""
import os
import json
import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime
import redis.asyncio as redis
from fastapi import WebSocket


class ConnectionManager:
    """
    Manages WebSocket connections and Redis Pub/Sub for real-time events.
    
    Architecture:
    - Frontend connects via WebSocket
    - Workers publish events to Redis channels
    - ConnectionManager subscribes to Redis and broadcasts to WebSocket clients
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # session_id -> WebSocket
        self.subscriptions: Dict[str, Set[str]] = {}  # channel -> set of session_ids
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self._listener_task: Optional[asyncio.Task] = None
        
    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection"""
        if self.redis is None:
            self.redis = redis.from_url(
                os.getenv("REDIS_URL", "redis://redis:6379"),
                decode_responses=True
            )
        return self.redis
    
    # --- WebSocket Management ---
    
    async def connect(self, websocket: WebSocket, session_id: str = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Generate session ID if not provided
        if not session_id:
            session_id = f"session-{datetime.utcnow().timestamp()}"
        
        self.active_connections[session_id] = websocket
        print(f"[WS] Client connected: {session_id}. Total: {len(self.active_connections)}")
        
        return session_id
    
    def disconnect(self, session_id: str):
        """Handle WebSocket disconnection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"[WS] Client disconnected: {session_id}. Total: {len(self.active_connections)}")
        
        # Clean up subscriptions
        for channel, sessions in self.subscriptions.items():
            sessions.discard(session_id)
    
    async def send_to_session(self, session_id: str, message: dict):
        """Send message to a specific session"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                print(f"[WS] Error sending to {session_id}: {e}")
                self.disconnect(session_id)
    
    async def broadcast(self, message: dict, exclude_session: str = None):
        """Broadcast message to all connected clients"""
        disconnected = []
        
        for session_id, websocket in self.active_connections.items():
            if exclude_session and session_id == exclude_session:
                continue
                
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"[WS] Error broadcasting to {session_id}: {e}")
                disconnected.append(session_id)
        
        # Clean up disconnected clients
        for session_id in disconnected:
            self.disconnect(session_id)
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """Broadcast message to clients subscribed to a channel"""
        if channel not in self.subscriptions:
            return
        
        for session_id in self.subscriptions[channel]:
            await self.send_to_session(session_id, message)
    
    # --- Subscription Management ---
    
    def subscribe_session(self, session_id: str, channel: str):
        """Subscribe a session to a channel (e.g., job_logs:job_123)"""
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
        self.subscriptions[channel].add(session_id)
        print(f"[WS] Session {session_id} subscribed to {channel}")
    
    def unsubscribe_session(self, session_id: str, channel: str):
        """Unsubscribe a session from a channel"""
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(session_id)
            print(f"[WS] Session {session_id} unsubscribed from {channel}")
    
    # --- Redis Pub/Sub ---
    
    async def subscribe_to_channels(self):
        """
        Subscribe to Redis channels and forward messages to WebSocket clients.
        This runs as a background task.
        """
        redis_client = await self._get_redis()
        self.pubsub = redis_client.pubsub()
        
        # Subscribe to all SentryAI channels
        channels = [
            "job_logs:*",       # Job log streams (pattern)
            "agent_events",     # Agent thought/plan events
            "scan_updates",     # Scan status updates
            "graph_updates",    # Neo4j graph changes
            "findings",         # New vulnerability findings
            "notifications",    # Integration notifications
        ]
        
        # Note: Redis pattern subscriptions use psubscribe
        await self.pubsub.psubscribe("job_logs:*")
        await self.pubsub.subscribe("agent_events", "scan_updates", "graph_updates", "findings", "notifications")
        
        print(f"[Redis] Subscribed to channels: {channels}")
        
        # Listen for messages
        async for message in self.pubsub.listen():
            if message["type"] in ("message", "pmessage"):
                await self._handle_redis_message(message)
    
    async def _handle_redis_message(self, message: dict):
        """Process incoming Redis message and route to WebSocket clients"""
        try:
            channel = message.get("channel") or message.get("pattern", "")
            data = message.get("data")
            
            # Parse JSON data
            if isinstance(data, str):
                data = json.loads(data)
            
            # Route based on channel
            if channel.startswith("job_logs:"):
                # Job-specific logs - send to subscribed sessions
                job_id = channel.split(":")[-1]
                await self.broadcast_to_channel(f"job_logs:{job_id}", {
                    "type": "server:job_log",
                    **data
                })
            
            elif channel == "agent_events":
                # Agent thoughts/plans - broadcast to all
                await self.broadcast({
                    "type": data.get("event_type", "server:agent_thought"),
                    **data
                })
            
            elif channel == "scan_updates":
                # Scan status updates
                await self.broadcast({
                    "type": "server:job_status",
                    **data
                })
            
            elif channel == "graph_updates":
                # Graph topology changes
                await self.broadcast({
                    "type": "server:graph_update",
                    **data
                })
            
            elif channel == "findings":
                # New vulnerabilities found
                await self.broadcast({
                    "type": "server:finding",
                    **data
                })
            
            elif channel == "notifications":
                # General notifications
                await self.broadcast({
                    "type": "server:notification",
                    **data
                })
            
            else:
                # Unknown channel - log and skip
                print(f"[Redis] Unknown channel: {channel}")
                
        except json.JSONDecodeError as e:
            print(f"[Redis] Failed to parse message: {e}")
        except Exception as e:
            print(f"[Redis] Error handling message: {e}")
    
    async def publish(self, channel: str, message: dict):
        """Publish a message to a Redis channel"""
        redis_client = await self._get_redis()
        await redis_client.publish(channel, json.dumps(message))
    
    # --- Convenience Methods for Workers ---
    
    async def publish_job_log(self, job_id: str, log: dict):
        """Publish a job log entry"""
        await self.publish(f"job_logs:{job_id}", {
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat(),
            **log
        })
    
    async def publish_agent_thought(self, step: str, log: str, status: str = "processing"):
        """Publish an agent thought event"""
        await self.publish("agent_events", {
            "event_type": "server:agent_thought",
            "step": step,
            "log": log,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def publish_plan_proposal(self, plan_id: str, intent: str, steps: list):
        """Publish a plan proposal for human-in-the-loop"""
        await self.publish("agent_events", {
            "event_type": "server:plan_proposal",
            "plan_id": plan_id,
            "intent": intent,
            "steps": steps,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def publish_scan_update(self, job_id: str, status: str, details: dict = None):
        """Publish a scan status update"""
        await self.publish("scan_updates", {
            "job_id": job_id,
            "status": status,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def publish_graph_update(self, event: str, data: dict):
        """Publish a graph topology update"""
        await self.publish("graph_updates", {
            "event": event,  # node_added, node_removed, edge_added, edge_removed
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def publish_finding(self, finding: dict):
        """Publish a new vulnerability finding"""
        await self.publish("findings", {
            **finding,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # --- Lifecycle ---
    
    async def start(self):
        """Start the connection manager (call on app startup)"""
        self._listener_task = asyncio.create_task(self.subscribe_to_channels())
        print("[EventManager] Started Redis listener")
    
    async def stop(self):
        """Stop the connection manager (call on app shutdown)"""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        if self.redis:
            await self.redis.close()
        
        print("[EventManager] Stopped")


# Singleton instance
manager = ConnectionManager()
