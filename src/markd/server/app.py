"""FastAPI application factory.

This module creates and configures the FastAPI application with:
- Router-based endpoint organization
- Dependency injection
- Middleware for security headers and caching
- Static file serving
- File watching and live reload
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from markd.config.models import ServerConfig
from markd.server.middleware import add_security_headers
from markd.server.routers.v1 import api, ui, ws
from markd.server.utils import setup_app_state

logger = logging.getLogger(__name__)


def create_app(config: ServerConfig) -> FastAPI:
    """Create and configure FastAPI application with router-based architecture.

    This function sets up:
    - Application lifespan management
    - State initialization (config, renderer, templates, WebSocket manager)
    - File watching for live reload
    - Security middleware
    - Static file serving
    - API, UI, and WebSocket routers

    Args:
        config: Server configuration

    Returns:
        Configured FastAPI application
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Handle application lifespan events.

        Startup: Initialize event loop and start file watcher
        Shutdown: Stop file watcher
        """
        # Startup: store event loop and start file watcher
        app.state.event_loop = asyncio.get_running_loop()

        if app.state.file_observer:
            app.state.file_observer.start()

        yield

        if app.state.file_observer:
            app.state.file_observer.stop()

    app = FastAPI(
        title="markd",
        description="Python based Markdown preview server with live reload",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Initialize app state, templates, static files, and file watcher
    setup_app_state(app, config)

    app.middleware("http")(add_security_headers)

    app.include_router(ui.router)
    app.include_router(api.router)
    app.include_router(ws.router)

    return app
