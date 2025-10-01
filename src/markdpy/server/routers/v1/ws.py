"""WebSocket router for live reload functionality.

This router handles the WebSocket endpoint for pushing live reload
notifications to connected clients.
"""

import logging

from fastapi import APIRouter, Depends, WebSocket

from markdpy.server.dependencies import get_ws_manager
from markdpy.server.websocket import ConnectionManager, websocket_endpoint

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_route(
    websocket: WebSocket,
    manager: ConnectionManager = Depends(get_ws_manager),
) -> None:
    """WebSocket endpoint for live reload notifications.

    Clients connect to this endpoint to receive real-time notifications
    when watched files change.

    Args:
        websocket: WebSocket connection
        manager: WebSocket connection manager (injected)
    """
    await websocket_endpoint(websocket, manager)
