"""Dependency injection for FastAPI endpoints.

This module provides dependency injection functions for accessing
application state and services in FastAPI route handlers.
"""

from pathlib import Path

from fastapi import Request, WebSocket
from fastapi.templating import Jinja2Templates

from markdpy.config.models import ServerConfig
from markdpy.renderer import MarkdownRenderer
from markdpy.server.websocket import ConnectionManager
from markdpy.watcher import FileObserver


def get_config(request: Request) -> ServerConfig:
    """Get server configuration from app state.

    Args:
        request: FastAPI request object

    Returns:
        Server configuration
    """
    return request.app.state.config


def get_renderer(request: Request) -> MarkdownRenderer:
    """Get markdown renderer from app state.

    Args:
        request: FastAPI request object

    Returns:
        Markdown renderer instance
    """
    return request.app.state.renderer


def get_templates(request: Request) -> Jinja2Templates:
    """Get Jinja2 templates from app state.

    Args:
        request: FastAPI request object

    Returns:
        Jinja2 templates instance
    """
    return request.app.state.templates


def get_ws_manager(websocket: WebSocket) -> ConnectionManager:
    """Get WebSocket connection manager from app state.

    Args:
        websocket: FastAPI WebSocket object

    Returns:
        Connection manager instance
    """
    return websocket.app.state.ws_manager


def get_file_observer(request: Request) -> FileObserver | None:
    """Get file observer from app state.

    Args:
        request: FastAPI request object

    Returns:
        File observer instance or None if not enabled
    """
    return request.app.state.file_observer


def get_serve_path(request: Request) -> Path:
    """Get serve path from configuration.

    Args:
        request: FastAPI request object

    Returns:
        Path being served
    """
    return request.app.state.config.serve_path


def get_validation_root(request: Request) -> Path:
    """Get validation root path for security checks.

    For single file mode, returns the parent directory to allow
    accessing sibling files like LICENSE.md when serving README.md.

    For directory mode, returns the serve path itself.

    Args:
        request: FastAPI request object

    Returns:
        Root path for validation
    """
    serve_path = request.app.state.config.serve_path
    return serve_path if serve_path.is_dir() else serve_path.parent


def get_theme(request: Request) -> str:
    """Get current theme from configuration.

    Args:
        request: FastAPI request object

    Returns:
        Theme name
    """
    return request.app.state.config.theme


def get_reload_enabled(request: Request) -> bool:
    """Get reload enabled status from configuration.

    Args:
        request: FastAPI request object

    Returns:
        True if live reload is enabled
    """
    return request.app.state.config.reload_enabled
