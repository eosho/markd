"""WebSocket connection manager for live reload functionality.

This module manages WebSocket connections for pushing live reload notifications
to connected clients when Markdown files change.
"""

import asyncio
import logging
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect

from ..config.models import WebSocketConnection

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for live reload.

    Tracks active connections and broadcasts reload messages when files change.
    Supports client-specific watched paths and heartbeat ping/pong.
    """

    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocketConnection] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
    ) -> WebSocketConnection:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            client_id: Unique identifier for this client

        Returns:
            WebSocketConnection instance for this client
        """
        await websocket.accept()

        connection = WebSocketConnection(
            client_id=client_id,
            websocket=websocket,
            watched_paths=set(),
        )

        async with self._lock:
            self.active_connections[client_id] = connection

        logger.info(f"WebSocket client connected: {client_id}")
        return connection

    async def disconnect(self, client_id: str) -> None:
        """Remove a connection from active connections.

        Args:
            client_id: Client to disconnect
        """
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
                logger.info(f"WebSocket client disconnected: {client_id}")

    async def send_reload(
        self,
        file_path: Path,
        client_id: str | None = None,
    ) -> None:
        """Send reload message to client(s).

        Args:
            file_path: Path to file that changed
            client_id: If provided, only send to this client; otherwise broadcast
        """
        async with self._lock:
            connections = list(self.active_connections.values())

        if client_id:
            # Send to specific client
            connection = next(
                (c for c in connections if c.client_id == client_id),
                None,
            )
            if connection:
                await connection.send_reload(file_path)
        else:
            # Broadcast to all clients watching this path
            tasks = []
            for connection in connections:
                # If no watched paths set, assume watching all files
                if not connection.watched_paths or file_path in connection.watched_paths:
                    tasks.append(connection.send_reload(file_path))

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                # Log any errors
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(
                            f"Error sending reload to {connections[i].client_id}: {result}"
                        )

    async def send_ping(self, client_id: str) -> None:
        """Send ping message to specific client for heartbeat.

        Args:
            client_id: Client to ping
        """
        async with self._lock:
            connection = self.active_connections.get(client_id)

        if connection:
            try:
                await connection.websocket.send_json({"type": "ping"})
            except Exception as e:
                logger.error(f"Error sending ping to {client_id}: {e}")

    async def register_watched_path(
        self,
        client_id: str,
        file_path: Path,
    ) -> None:
        """Register a file path that a client wants to watch.

        Args:
            client_id: Client registering the path
            file_path: Path to watch for changes
        """
        async with self._lock:
            connection = self.active_connections.get(client_id)
            if connection:
                connection.watched_paths.add(file_path)
                logger.debug(f"Client {client_id} watching: {file_path}")

    def get_count(self) -> int:
        """Get number of active connections.

        Returns:
            Number of connected clients
        """
        return len(self.active_connections)


async def websocket_endpoint(
    websocket: WebSocket,
    manager: ConnectionManager,
) -> None:
    """WebSocket endpoint handler for live reload connections.

    Accepts WebSocket connections, handles incoming messages (pong, watch),
    and manages the connection lifecycle.

    Args:
        websocket: FastAPI WebSocket instance
        manager: ConnectionManager instance
    """
    # Generate client ID from websocket
    client_id = f"{websocket.client.host}:{websocket.client.port}"  # type: ignore[union-attr]

    connection = await manager.connect(websocket, client_id)

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "pong":
                # Client responded to ping - connection alive
                logger.debug(f"Received pong from {client_id}")

            elif message_type == "watch":
                # Client wants to watch a specific file
                file_path_str = data.get("path")
                if file_path_str:
                    file_path = Path(file_path_str)
                    await manager.register_watched_path(client_id, file_path)

            elif message_type == "unwatch":
                # Client no longer watching a file
                file_path_str = data.get("path")
                if file_path_str:
                    file_path = Path(file_path_str)
                    if file_path in connection.watched_paths:
                        connection.watched_paths.remove(file_path)
                        logger.debug(f"Client {client_id} stopped watching: {file_path}")

            else:
                logger.warning(f"Unknown message type from {client_id}: {message_type}")

    except WebSocketDisconnect:
        await manager.disconnect(client_id)

    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        await manager.disconnect(client_id)


async def heartbeat_task(manager: ConnectionManager) -> None:
    """Background task to send periodic ping messages to all connections.

    Args:
        manager: ConnectionManager instance
    """
    while True:
        await asyncio.sleep(30)  # Ping every 30 seconds

        # Get snapshot of client IDs
        client_ids = list(manager.active_connections.keys())

        for client_id in client_ids:
            await manager.send_ping(client_id)
