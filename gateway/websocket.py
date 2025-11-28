"""
WebSocket Server for OsMEN Real-time Updates

Provides WebSocket connections for real-time updates to dashboards.
Supports multi-client broadcast, reconnection handling, and room-based subscriptions.

Usage:
    from gateway.websocket import get_websocket_manager
    
    manager = get_websocket_manager()
    
    # In your FastAPI app
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            await manager.handle_messages(websocket)
        finally:
            manager.disconnect(websocket)
    
    # Broadcast updates
    await manager.broadcast({"type": "run_update", "data": {...}})
    await manager.broadcast_to_room("run:123", {"type": "step", "data": {...}})
"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types"""
    # Client -> Server
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"
    
    # Server -> Client
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    PONG = "pong"
    ERROR = "error"
    
    # Broadcast messages
    RUN_CREATED = "run_created"
    RUN_STARTED = "run_started"
    RUN_STEP = "run_step"
    RUN_TOOL_CALL = "run_tool_call"
    RUN_TOOL_RESULT = "run_tool_result"
    RUN_APPROVAL_REQUIRED = "run_approval_required"
    RUN_APPROVAL_RESPONSE = "run_approval_response"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"
    RUN_CANCELLED = "run_cancelled"
    
    STATS_UPDATE = "stats_update"
    WORKFLOW_UPDATE = "workflow_update"


@dataclass
class WebSocketClient:
    """Represents a connected WebSocket client"""
    id: str
    websocket: Any  # WebSocket instance
    connected_at: datetime
    rooms: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    async def send(self, message: Dict[str, Any]):
        """Send message to this client"""
        try:
            await self.websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send to client {self.id}: {e}")
            raise


class WebSocketManager:
    """
    Manages WebSocket connections and message broadcasting.
    
    Features:
    - Multi-client connection management
    - Room-based subscriptions
    - Heartbeat monitoring
    - Message history for catch-up
    - Automatic reconnection handling
    """
    
    def __init__(
        self,
        heartbeat_interval: float = 30.0,
        max_history: int = 100
    ):
        """
        Initialize WebSocket manager.
        
        Args:
            heartbeat_interval: Seconds between heartbeat pings
            max_history: Maximum messages to keep for catch-up
        """
        self.heartbeat_interval = heartbeat_interval
        self.max_history = max_history
        
        # Connected clients by ID
        self._clients: Dict[str, WebSocketClient] = {}
        
        # Room subscriptions: room_name -> set of client_ids
        self._rooms: Dict[str, Set[str]] = defaultdict(set)
        
        # Message history for catch-up: room_name -> list of messages
        self._history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Message handlers
        self._handlers: Dict[str, Callable] = {}
        
        # Heartbeat tasks
        self._heartbeat_tasks: Dict[str, asyncio.Task] = {}
        
        # Statistics
        self._stats = {
            "total_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0
        }
    
    async def connect(
        self,
        websocket: Any,
        client_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: WebSocket instance
            client_id: Optional client ID (generated if not provided)
            metadata: Optional client metadata
            
        Returns:
            Client ID
        """
        await websocket.accept()
        
        client_id = client_id or str(uuid4())
        
        client = WebSocketClient(
            id=client_id,
            websocket=websocket,
            connected_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        self._clients[client_id] = client
        self._stats["total_connections"] += 1
        
        # Start heartbeat
        self._start_heartbeat(client_id)
        
        # Subscribe to global room by default
        await self.subscribe(client_id, "global")
        
        logger.info(f"WebSocket client connected: {client_id}")
        
        # Send connection confirmation
        await self.send_to_client(client_id, {
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return client_id
    
    def disconnect(self, websocket: Any):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket instance to remove
        """
        # Find client by websocket
        client_id = None
        for cid, client in self._clients.items():
            if client.websocket == websocket:
                client_id = cid
                break
        
        if client_id:
            self._disconnect_client(client_id)
    
    def _disconnect_client(self, client_id: str):
        """Disconnect client by ID"""
        if client_id not in self._clients:
            return
        
        client = self._clients[client_id]
        
        # Unsubscribe from all rooms
        for room in list(client.rooms):
            self._rooms[room].discard(client_id)
            if not self._rooms[room]:
                del self._rooms[room]
        
        # Stop heartbeat
        self._stop_heartbeat(client_id)
        
        # Remove client
        del self._clients[client_id]
        
        logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def subscribe(self, client_id: str, room: str):
        """
        Subscribe client to a room.
        
        Args:
            client_id: Client ID
            room: Room name
        """
        if client_id not in self._clients:
            return
        
        self._clients[client_id].rooms.add(room)
        self._rooms[room].add(client_id)
        
        # Send confirmation
        await self.send_to_client(client_id, {
            "type": MessageType.SUBSCRIBED.value,
            "room": room
        })
        
        # Send history for catch-up
        if room in self._history:
            for msg in self._history[room][-10:]:  # Last 10 messages
                await self.send_to_client(client_id, msg)
    
    async def unsubscribe(self, client_id: str, room: str):
        """
        Unsubscribe client from a room.
        
        Args:
            client_id: Client ID
            room: Room name
        """
        if client_id not in self._clients:
            return
        
        self._clients[client_id].rooms.discard(room)
        self._rooms[room].discard(client_id)
        
        if not self._rooms[room]:
            del self._rooms[room]
        
        await self.send_to_client(client_id, {
            "type": MessageType.UNSUBSCRIBED.value,
            "room": room
        })
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """
        Send message to specific client.
        
        Args:
            client_id: Client ID
            message: Message to send
        """
        if client_id not in self._clients:
            return
        
        try:
            await self._clients[client_id].send(message)
            self._stats["total_messages_sent"] += 1
        except Exception as e:
            logger.warning(f"Failed to send to {client_id}: {e}")
            self._disconnect_client(client_id)
    
    async def broadcast(self, message: Dict[str, Any], exclude: Optional[Set[str]] = None):
        """
        Broadcast message to all connected clients.
        
        Args:
            message: Message to broadcast
            exclude: Optional set of client IDs to exclude
        """
        exclude = exclude or set()
        
        for client_id in list(self._clients.keys()):
            if client_id not in exclude:
                await self.send_to_client(client_id, message)
        
        # Store in global history
        self._add_to_history("global", message)
    
    async def broadcast_to_room(
        self,
        room: str,
        message: Dict[str, Any],
        exclude: Optional[Set[str]] = None
    ):
        """
        Broadcast message to all clients in a room.
        
        Args:
            room: Room name
            message: Message to broadcast
            exclude: Optional set of client IDs to exclude
        """
        exclude = exclude or set()
        
        for client_id in self._rooms.get(room, set()):
            if client_id not in exclude:
                await self.send_to_client(client_id, message)
        
        # Store in room history
        self._add_to_history(room, message)
    
    async def handle_messages(self, websocket: Any):
        """
        Handle incoming messages from a WebSocket.
        
        Args:
            websocket: WebSocket instance
        """
        # Find client
        client_id = None
        for cid, client in self._clients.items():
            if client.websocket == websocket:
                client_id = cid
                break
        
        if not client_id:
            return
        
        try:
            while True:
                data = await websocket.receive_json()
                self._stats["total_messages_received"] += 1
                
                await self._handle_message(client_id, data)
        except Exception as e:
            logger.debug(f"WebSocket receive error for {client_id}: {e}")
    
    async def _handle_message(self, client_id: str, data: Dict[str, Any]):
        """Handle a single message from a client"""
        msg_type = data.get("type")
        
        if msg_type == MessageType.SUBSCRIBE.value:
            room = data.get("room")
            if room:
                await self.subscribe(client_id, room)
        
        elif msg_type == MessageType.UNSUBSCRIBE.value:
            room = data.get("room")
            if room:
                await self.unsubscribe(client_id, room)
        
        elif msg_type == MessageType.PING.value:
            await self.send_to_client(client_id, {
                "type": MessageType.PONG.value,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif msg_type in self._handlers:
            await self._handlers[msg_type](client_id, data)
    
    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type"""
        self._handlers[message_type] = handler
    
    def _add_to_history(self, room: str, message: Dict[str, Any]):
        """Add message to room history"""
        message["_timestamp"] = datetime.utcnow().isoformat()
        self._history[room].append(message)
        
        # Trim history
        if len(self._history[room]) > self.max_history:
            self._history[room] = self._history[room][-self.max_history:]
    
    def _start_heartbeat(self, client_id: str):
        """Start heartbeat task for a client"""
        async def heartbeat_loop():
            while client_id in self._clients:
                await asyncio.sleep(self.heartbeat_interval)
                try:
                    await self.send_to_client(client_id, {
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception:
                    self._disconnect_client(client_id)
                    break
        
        task = asyncio.create_task(heartbeat_loop())
        self._heartbeat_tasks[client_id] = task
    
    def _stop_heartbeat(self, client_id: str):
        """Stop heartbeat task for a client"""
        if client_id in self._heartbeat_tasks:
            self._heartbeat_tasks[client_id].cancel()
            del self._heartbeat_tasks[client_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket statistics"""
        return {
            **self._stats,
            "active_connections": len(self._clients),
            "rooms": list(self._rooms.keys()),
            "rooms_count": len(self._rooms)
        }
    
    def get_room_clients(self, room: str) -> List[str]:
        """Get client IDs in a room"""
        return list(self._rooms.get(room, set()))
    
    def get_client_rooms(self, client_id: str) -> List[str]:
        """Get rooms a client is subscribed to"""
        if client_id not in self._clients:
            return []
        return list(self._clients[client_id].rooms)


# Global instance
_manager: Optional[WebSocketManager] = None

def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance"""
    global _manager
    if _manager is None:
        _manager = WebSocketManager()
    return _manager


# Integration with streaming and storage
class WebSocketBroadcaster:
    """
    Broadcasts events from StreamingManager and RunStorage to WebSocket clients.
    
    Automatically subscribes to events and forwards them to connected clients.
    """
    
    def __init__(self):
        self.ws_manager = get_websocket_manager()
    
    def setup_streaming_integration(self, streaming_manager):
        """
        Integrate with StreamingManager to forward SSE events to WebSocket.
        
        Args:
            streaming_manager: StreamingManager instance
        """
        def on_event(event):
            # Create WebSocket message from SSE event
            message = {
                "type": event.event_type.value,
                "run_id": event.run_id,
                "timestamp": event.timestamp,
                "data": event.data,
                "sequence": event.sequence
            }
            
            # Broadcast to run-specific room
            asyncio.create_task(
                self.ws_manager.broadcast_to_room(
                    f"run:{event.run_id}",
                    message
                )
            )
            
            # Also broadcast to global for dashboard updates
            asyncio.create_task(
                self.ws_manager.broadcast({
                    "type": "run_event",
                    "run_id": event.run_id,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp
                })
            )
        
        streaming_manager.register_event_handler(on_event)
        logger.info("WebSocket integration with StreamingManager established")
    
    async def broadcast_stats_update(self, stats: Dict[str, Any]):
        """Broadcast statistics update to all clients"""
        await self.ws_manager.broadcast({
            "type": MessageType.STATS_UPDATE.value,
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def notify_run_created(self, run_id: str, workflow_name: str):
        """Notify clients of new run"""
        await self.ws_manager.broadcast({
            "type": MessageType.RUN_CREATED.value,
            "run_id": run_id,
            "workflow_name": workflow_name,
            "timestamp": datetime.utcnow().isoformat()
        })


# FastAPI integration
try:
    from fastapi import APIRouter, WebSocket, WebSocketDisconnect
    
    router = APIRouter(tags=["websocket"])
    
    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """
        Main WebSocket endpoint for real-time updates.
        
        Messages:
        - subscribe: {"type": "subscribe", "room": "run:123"}
        - unsubscribe: {"type": "unsubscribe", "room": "run:123"}
        - ping: {"type": "ping"}
        """
        manager = get_websocket_manager()
        
        try:
            client_id = await manager.connect(websocket)
            await manager.handle_messages(websocket)
        except WebSocketDisconnect:
            pass
        finally:
            manager.disconnect(websocket)
    
    @router.get("/ws/stats")
    async def websocket_stats():
        """Get WebSocket connection statistics"""
        manager = get_websocket_manager()
        return manager.get_stats()
    
    @router.get("/ws/rooms")
    async def list_rooms():
        """List active WebSocket rooms"""
        manager = get_websocket_manager()
        stats = manager.get_stats()
        return {
            "rooms": stats["rooms"],
            "count": stats["rooms_count"]
        }

except ImportError:
    router = None


# Export
__all__ = [
    "WebSocketManager",
    "WebSocketClient",
    "WebSocketBroadcaster",
    "MessageType",
    "get_websocket_manager",
    "router"
]
