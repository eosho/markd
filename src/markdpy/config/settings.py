"""Application settings and configuration."""

import os

from markdpy.config.models import VALID_THEMES, RenderConfig

# Default settings
DEFAULT_HOST = os.getenv("HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("PORT", "8000"))
DEFAULT_THEME = os.getenv("THEME", "light")
DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Rendering defaults
DEFAULT_RENDER_CONFIG = RenderConfig.default()

# File size limits
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Debounce settings for file watcher
DEBOUNCE_DELAY_MS = 150
DEBOUNCE_DELAY_SECONDS = DEBOUNCE_DELAY_MS / 1000

# WebSocket settings
WEBSOCKET_PING_INTERVAL = 30  # seconds
WEBSOCKET_TIMEOUT = 60  # seconds

# Cache settings
RENDER_CACHE_SIZE = 128  # Max number of rendered files to cache

__all__ = [
    "VALID_THEMES",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "DEFAULT_THEME",
    "DEFAULT_LOG_LEVEL",
    "DEFAULT_RENDER_CONFIG",
    "MAX_FILE_SIZE_BYTES",
    "DEBOUNCE_DELAY_SECONDS",
    "WEBSOCKET_PING_INTERVAL",
    "WEBSOCKET_TIMEOUT",
    "RENDER_CACHE_SIZE",
]
