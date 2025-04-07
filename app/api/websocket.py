"""
WebSocket connection management for the Odoo Dev Server Monitoring Tool.
"""
from fastapi import WebSocket
from typing import List


class ConnectionManager:
    """
    Manager for WebSocket connections.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Connect a new WebSocket client.

        Args:
            websocket: The WebSocket connection to accept
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a WebSocket client.

        Args:
            websocket: The WebSocket connection to disconnect
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        Send a message to a specific client.

        Args:
            message: The message to send
            websocket: The WebSocket connection to send to
        """
        if websocket.client_state.CONNECTED:
            await websocket.send_text(message)

    async def send_personal_json(self, data: dict, websocket: WebSocket):
        """
        Send JSON data to a specific client.

        Args:
            data: The data to send
            websocket: The WebSocket connection to send to
        """
        if websocket.client_state.CONNECTED:
            await websocket.send_json(data)

    async def broadcast(self, message: str):
        """
        Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Mark for disconnection if sending fails
                disconnected.append(connection)

        # Clean up any disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_json(self, data: dict):
        """
        Broadcast JSON data to all connected clients.

        Args:
            data: The data to broadcast
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                # Mark for disconnection if sending fails
                disconnected.append(connection)

        # Clean up any disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
