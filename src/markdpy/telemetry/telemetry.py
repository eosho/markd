"""
Telemetry client for the `markdpy` project.

This module defines lightweight, anonymous telemetry for tracking
aggregate usage statistics such as number of renders, errors, and
average render latency. Telemetry is enabled by default, but can be
disabled by the user either programmatically or via the environment
variable `TELEMETRY=0`.

Collected metrics are anonymous and minimal:
    • An install ID (UUID generated locally once)
    • Application version (passed by the caller)
    • Python runtime version
    • Operating system name
    • Counts of renders and errors
    • Average render latency (ms) since last flush

Telemetry is persisted locally in a small JSON file inside the user
configuration directory (e.g., ~/.config/markdpy/telemetry.json).

Usage:
    >>> telemetry = TelemetryClient(version="1.0.0")
    >>> telemetry.track_render(12.3)
    >>> telemetry.track_error()
    >>> telemetry.flush()   # manually force flush before shutdown
"""

from __future__ import annotations

import json
import os
import platform
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx
from platformdirs import user_config_dir


@dataclass
class TelemetryState:
    """
    Persistent state for telemetry.

    Attributes:
        install_id (str): Anonymous UUID identifying this installation.
        enabled (bool): Whether telemetry is enabled. Defaults to True.
        last_sent (Optional[str]): ISO8601 timestamp of last flush, if any.
    """

    install_id: str
    enabled: bool = True
    last_sent: str | None = None


@dataclass
class TelemetryEvents:
    """
    In-memory counters representing usage events.

    Attributes:
        renders (int): Number of render operations since last flush.
        errors (int): Number of errors since last flush.
        avg_render_ms (Optional[float]): Average render latency in ms.
    """

    renders: int = 0
    errors: int = 0
    avg_render_ms: float | None = None


@dataclass
class TelemetryPayload:
    """
    Telemetry payload to be sent to the ingestion endpoint.

    Attributes:
        install_id (str): Anonymous UUID of this installation.
        version (str): Version string of the application (markdpy).
        os (str): Operating system name (Linux, Darwin, Windows, etc.).
        python (str): Python runtime version.
        events (TelemetryEvents): Aggregate counters.
    """

    install_id: str
    version: str
    os: str
    python: str
    events: TelemetryEvents


class TelemetryClient:
    """Anonymous telemetry client for the `markdpy` project."""

    ENDPOINT = "https://telemetry.markdpy.dev/api/telemetry"
    FLUSH_INTERVAL = 60  # seconds

    def __init__(self, version: str) -> None:
        """
        Initialize a new TelemetryClient.

        Args:
            version (str): Version string of the calling application.
        """
        self.version = version
        self.config_path = Path(user_config_dir("markdpy")) / "telemetry.json"
        self.state: TelemetryState = self._load_or_init()

        self._renders: list[float] = []
        self._errors = 0
        self._last_flush = 0

        # Environment variable override (disable telemetry)
        if os.getenv("TELEMETRY", "1") == "0":
            self.state.enabled = False

    def is_enabled(self) -> bool:
        """Return True if telemetry is enabled, False otherwise."""
        return self.state.enabled

    def disable(self) -> None:
        """Disable telemetry permanently and persist the state to disk."""
        self.state.enabled = False
        self._save()

    def track_render(self, latency_ms: float) -> None:
        """
        Record a render event.

        Args:
            latency_ms (float): Time taken for the render, in milliseconds.
        """
        if not self.is_enabled():
            return
        self._renders.append(latency_ms)
        self._maybe_flush()

    def track_error(self) -> None:
        """Record an error event."""
        if not self.is_enabled():
            return
        self._errors += 1
        self._maybe_flush()

    def flush(self) -> bool:
        """
        Build and send a telemetry payload with current metrics.

        This will reset in-memory counters after attempting to send.
        The client will fail silently if the network is unavailable.

        Returns:
            bool: True if data was processed and sent, False if no action taken.
        """
        if not self.is_enabled():
            return False

        if not self._renders and self._errors == 0:
            return False

        avg_latency = None
        if self._renders:
            avg_latency = sum(self._renders) / len(self._renders)

        payload = TelemetryPayload(
            install_id=self.state.install_id,
            version=self.version,
            os=platform.system(),
            python=platform.python_version(),
            events=TelemetryEvents(
                renders=len(self._renders),
                errors=self._errors,
                avg_render_ms=avg_latency,
            ),
        )

        try:
            httpx.post(self.ENDPOINT, json=asdict(payload), timeout=3.0)
        except Exception:
            pass  # never crash the app

        # reset counters
        self._renders.clear()
        self._errors = 0
        self.state.last_sent = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._save()

        return True

    # -----------------------
    # Internal helpers
    # -----------------------
    def _load_or_init(self) -> TelemetryState:
        """
        Load telemetry state from disk, or create a new one if missing
        or corrupted.

        Returns:
            TelemetryState: Current telemetry state object.
        """
        if not self.config_path.exists():
            state = TelemetryState(install_id=str(uuid.uuid4()))
            self._write_state(state)
            return state
        try:
            raw = json.loads(self.config_path.read_text())
            return TelemetryState(**raw)
        except Exception:
            state = TelemetryState(install_id=str(uuid.uuid4()))
            self._write_state(state)
            return state

    def _save(self) -> None:
        """Persist the current telemetry state to disk."""
        self._write_state(self.state)

    def _write_state(self, state: TelemetryState) -> None:
        """Write a TelemetryState object to the JSON config file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(json.dumps(asdict(state), indent=2))
        except Exception:
            pass

    def _maybe_flush(self) -> None:
        """
        Flush metrics if enough time has passed since the last flush.
        """
        now = time.time()
        if now - self._last_flush > self.FLUSH_INTERVAL:
            try:
                success = self.flush()
                # Only update _last_flush if flush actually processed data
                if success:
                    self._last_flush = now
            except Exception:
                pass
