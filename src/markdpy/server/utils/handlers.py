"""Event handlers for file system changes and WebSocket notifications.

This module contains handlers for processing file system events
and coordinating with the WebSocket manager to notify clients.
"""

import asyncio
import logging

from fastapi import FastAPI

from markdpy.config.models import WatcherEvent
from markdpy.server.websocket import ConnectionManager

logger = logging.getLogger(__name__)


def handle_file_change(app: FastAPI, event: WatcherEvent) -> None:
    """Handle file system change events by notifying WebSocket clients.

    This function is called by the file observer when a watched file changes.
    It checks if the change should trigger a reload and notifies all connected
    WebSocket clients if necessary.

    Args:
        app: FastAPI application instance
        event: File system event containing change details
    """
    logger.debug(f"File change detected: {event.file_path} (type: {event.event_type})")

    if event.should_trigger_reload():
        logger.info(f"Should trigger reload for: {event.file_path}")

        # Broadcast reload to all connected clients
        # Use the event loop stored during lifespan startup
        manager: ConnectionManager = app.state.ws_manager
        loop = getattr(app.state, "event_loop", None)

        logger.debug(
            f"Event loop exists: {loop is not None}, WebSocket connections: {manager.get_count()}"
        )

        if loop and loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    manager.send_reload(event.file_path), loop
                )
                # Wait briefly to ensure it's scheduled
                future.result(timeout=0.5)
                logger.info(f"✓ Triggered reload for: {event.file_path}")
            except Exception as e:
                logger.error(f"✗ Failed to trigger reload: {e}")
        else:
            logger.warning("Cannot trigger reload - event loop unavailable or not running")
