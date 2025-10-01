"""File system observer for monitoring Markdown files.

This module implements a file watcher using watchdog that monitors a directory
for changes to Markdown files and triggers callbacks.
"""

import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from watchdog.events import (
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from ..config.models import WatcherEvent

logger = logging.getLogger(__name__)


class DebouncedEventHandler(FileSystemEventHandler):
    """File system event handler with simple time-based debouncing.

    Handles file system events and triggers callbacks for Markdown file changes,
    with simple debouncing based on time since last event.

    Args:
        callback: Function to call with WatcherEvent when file changes
        debounce_ms: Milliseconds to wait between events for same file
    """

    def __init__(
        self,
        callback: Callable[[WatcherEvent], Any],
        debounce_ms: int = 150,
    ) -> None:
        super().__init__()
        self.callback = callback
        self.debounce_ms = debounce_ms
        self._last_event_time: dict[Path, float] = {}

    def on_any_event(self, event: FileSystemEvent) -> None:
        """Handle any file system event.

        Args:
            event: Watchdog file system event
        """
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))

        # Only track Markdown files
        if file_path.suffix.lower() not in {".md", ".markdown"}:
            return

        # Convert watchdog event type to our event type
        event_type_map = {
            "created": "created",
            "modified": "modified",
            "deleted": "deleted",
            "moved": "modified",  # Treat moves as modifications
        }

        event_type = event_type_map.get(event.event_type, "modified")
        watcher_event = WatcherEvent(
            event_type=event_type,  # type: ignore[arg-type]
            file_path=file_path,
            timestamp=time.time(),
        )

        # Simple time-based debouncing
        now = time.time()
        last_time = self._last_event_time.get(file_path, 0.0)

        if now - last_time >= (self.debounce_ms / 1000.0):
            self._last_event_time[file_path] = now
            # Call callback directly (it handles async execution if needed)
            self.callback(watcher_event)


class FileObserver:
    """High-level file system observer for monitoring directories.

    Wraps watchdog Observer with a debounced event handler for tracking
    changes to Markdown files in a directory tree.

    Args:
        watch_path: Directory path to monitor
        callback: Function to call with WatcherEvent when files change
        debounce_ms: Milliseconds to wait between events for same file
        recursive: Whether to monitor subdirectories
    """

    def __init__(
        self,
        watch_path: Path,
        callback: Callable[[WatcherEvent], Any],
        debounce_ms: int = 150,
        recursive: bool = True,
    ) -> None:
        self.watch_path = watch_path.resolve()
        self.callback = callback
        self.debounce_ms = debounce_ms
        self.recursive = recursive

        self._observer: Observer | None = None  # type: ignore
        self._event_handler = None  # Will be DebouncedEventHandler when started

    def start(self) -> None:
        """Start monitoring the directory for changes."""
        if self._observer is not None:
            logger.warning("File observer already started")
            return

        self._event_handler = DebouncedEventHandler(
            callback=self.callback,
            debounce_ms=self.debounce_ms,
        )

        observer = Observer()
        observer.schedule(
            self._event_handler,
            str(self.watch_path),
            recursive=self.recursive,
        )
        observer.start()
        self._observer = observer

        logger.info(
            f"File observer started: watching {self.watch_path} "
            f"(recursive={self.recursive}, debounce={self.debounce_ms}ms)"
        )

    def stop(self) -> None:
        """Stop monitoring the directory."""
        if self._observer is None:
            logger.warning("File observer not started")
            return

        self._observer.stop()
        self._observer.join(timeout=5.0)
        self._observer = None
        self._event_handler = None

        logger.info("File observer stopped")

    def is_running(self) -> bool:
        """Check if the observer is currently running.

        Returns:
            True if observer is running, False otherwise
        """
        return self._observer is not None and self._observer.is_alive()

    def __enter__(self) -> "FileObserver":
        """Context manager entry: start the observer."""
        self.start()
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit: stop the observer."""
        self.stop()
