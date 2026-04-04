from fastapi import WebSocket
from typing import Dict, Set
import asyncio
import json

class WebSocketManager:
    def __init__(self):
        # Store connections by channel: {"prices": set(), "signals": set()}
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "prices": set(),
            "signals": set()
        }

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel in self.active_connections:
            self.active_connections[channel].add(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a single websocket client."""
        try:
            await websocket.send_text(message)
        except Exception:
            pass # Client likely disconnected during handshake

    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)

    async def broadcast(self, message: str, channel: str):
        """Send message to all clients in a specific channel."""
        if channel not in self.active_connections:
            return

        disconnected_clients = []
        for connection in self.active_connections[channel]:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected_clients.append(connection)

        for client in disconnected_clients:
            self.disconnect(client, channel)

# Global singleton
manager = WebSocketManager()
