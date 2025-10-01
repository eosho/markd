"""Telemetry module for anonymous usage tracking."""

from .telemetry import TelemetryClient, TelemetryEvents, TelemetryPayload, TelemetryState

# Global telemetry client instance - initialized during app startup
_telemetry_client: TelemetryClient | None = None


def init_telemetry(version: str) -> None:
    """Initialize the global telemetry client.

    Args:
        version: Application version string
    """
    global _telemetry_client
    _telemetry_client = TelemetryClient(version=version)


def get_telemetry() -> TelemetryClient | None:
    """Get the global telemetry client instance.

    Returns:
        TelemetryClient instance if initialized, None otherwise
    """
    return _telemetry_client


def track_render(latency_ms: float) -> None:
    """Track a render event.

    Args:
        latency_ms: Render latency in milliseconds
    """
    if _telemetry_client:
        _telemetry_client.track_render(latency_ms)


def track_error() -> None:
    """Track an error event."""
    if _telemetry_client:
        _telemetry_client.track_error()


def flush() -> bool:
    """Flush pending telemetry data.

    Returns:
        bool: True if data was processed and sent, False if no action taken.
    """
    if _telemetry_client:
        return _telemetry_client.flush()
    return False


__all__ = [
    "TelemetryClient",
    "TelemetryEvents",
    "TelemetryPayload",
    "TelemetryState",
    "init_telemetry",
    "get_telemetry",
    "track_render",
    "track_error",
    "flush",
]
