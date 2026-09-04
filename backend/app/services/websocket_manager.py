import asyncio
import json
from typing import Any, Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections for event feeds and incident alerts."""

    def __init__(self):
        self.event_connections: List[WebSocket] = []
        self.incident_connections: List[WebSocket] = []

    async def connect_event(self, websocket: WebSocket):
        await websocket.accept()
        self.event_connections.append(websocket)

    def disconnect_event(self, websocket: WebSocket):
        if websocket in self.event_connections:
            self.event_connections.remove(websocket)

    async def connect_incident(self, websocket: WebSocket):
        await websocket.accept()
        self.incident_connections.append(websocket)

    def disconnect_incident(self, websocket: WebSocket):
        if websocket in self.incident_connections:
            self.incident_connections.remove(websocket)

    async def broadcast_event(self, data: Dict[str, Any]):
        """Broadcast live event data to all connected event WebSocket clients."""
        payload = json.dumps(data, default=str)
        to_remove = []
        for connection in list(self.event_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                to_remove.append(connection)
        for dead in to_remove:
            self.disconnect_event(dead)

    async def broadcast_incident(self, data: Dict[str, Any]):
        """Broadcast live safety incident alert to all connected incident WebSocket clients."""
        payload = json.dumps(data, default=str)
        to_remove = []
        for connection in list(self.incident_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                to_remove.append(connection)
        for dead in to_remove:
            self.disconnect_incident(dead)

    def get_total_active_connections(self) -> int:
        return len(self.event_connections) + len(self.incident_connections)


ws_manager = ConnectionManager()
