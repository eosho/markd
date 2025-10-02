"""Core data models for markdpy."""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Valid theme names
VALID_THEMES = ["light", "dark", "catppuccin-mocha", "catppuccin-latte"]


@dataclass
class MarkdownFile:
    """Represents a Markdown file in the file system."""

    path: Path
    relative_path: Path
    content: str
    content_hash: str
    rendered_html: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    modified_time: float = 0.0
    file_size: int = 0

    def needs_rerender(self) -> bool:
        """Check if file content changed since last render."""
        current_hash = hashlib.sha256(self.content.encode()).hexdigest()
        return current_hash != self.content_hash

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON responses."""
        return {
            "path": str(self.relative_path),
            "size": self.file_size,
            "modified": self.modified_time,
        }


@dataclass
class DirectoryListing:
    """Represents a directory with Markdown files."""

    path: Path
    relative_path: Path
    files: list[MarkdownFile] = field(default_factory=list)
    subdirectories: list["DirectoryListing"] = field(default_factory=list)
    index_file: MarkdownFile | None = None

    def get_file_tree(self) -> dict[str, Any]:
        """Generate hierarchical file tree for sidebar."""
        return {
            "name": self.path.name,
            "path": str(self.relative_path),
            "files": [f.to_dict() for f in self.files],
            "subdirs": [d.get_file_tree() for d in self.subdirectories],
        }

    def find_file(self, relative_path: Path) -> MarkdownFile | None:
        """Find file by relative path in tree."""
        # Check files in current directory
        for file in self.files:
            if file.relative_path == relative_path:
                return file

        # Check subdirectories
        for subdir in self.subdirectories:
            result = subdir.find_file(relative_path)
            if result:
                return result

        return None


@dataclass
class RenderConfig:
    """Configuration for Markdown renderer."""

    extensions: list[str] = field(default_factory=list)
    extension_configs: dict[str, Any] = field(default_factory=dict)
    syntax_theme: str = "monokai"
    enable_toc: bool = True
    toc_depth: int = 3
    enable_math: bool = True
    enable_mermaid: bool = True
    enable_emoji: bool = True

    @classmethod
    def default(cls) -> "RenderConfig":
        """Create default configuration with rich Markdown + pymdownx support."""
        return cls(
            extensions=[
                # --- Core markdown extensions ---
                "markdown.extensions.abbr",
                "markdown.extensions.attr_list",
                "markdown.extensions.def_list",
                "markdown.extensions.footnotes",
                "markdown.extensions.meta",
                "markdown.extensions.sane_lists",
                "markdown.extensions.smarty",
                "markdown.extensions.tables",
                "markdown.extensions.nl2br",
                "markdown.extensions.fenced_code",
                "markdown.extensions.codehilite",
                "markdown.extensions.toc",
                # --- pymdownx extensions ---
                "pymdownx.highlight",
                "pymdownx.inlinehilite",
                "pymdownx.superfences",
                "pymdownx.tasklist",
                "pymdownx.emoji",
                "pymdownx.mark",
                "pymdownx.tilde",
                "pymdownx.caret",
                "pymdownx.details",
                "pymdownx.keys",
                "pymdownx.magiclink",
                "pymdownx.progressbar",
                "pymdownx.snippets",
                "pymdownx.escapeall",
                "pymdownx.arithmatex",
            ],
            extension_configs={
                "codehilite": {
                    "css_class": "highlight",
                    "guess_lang": False,
                    "linenums": False,
                    "noinlinestyles": True,
                },
                "toc": {
                    "permalink": True,
                    "baselevel": 1,
                },
                "pymdownx.tasklist": {
                    "custom_checkbox": True,
                },
                "pymdownx.emoji": {
                    "emoji_generator": "github",
                },
                "pymdownx.magiclink": {
                    "repo_url_shortener": True,
                    "hide_protocol": True,
                },
                "pymdownx.highlight": {
                    "anchor_linenums": False,
                    "use_pygments": True,
                    "pygments_lang_class": True,
                },
                "pymdownx.arithmatex": {
                    "generic": True,  # works with MathJax/KaTeX
                },
                "pymdownx.snippets": {
                    "check_paths": True,
                },
                "pymdownx.superfences": {
                    "custom_fences": [
                        {
                            "name": "mermaid",
                            "class": "mermaid",
                            "format": lambda src,
                            *args,
                            **kwargs: f'<div class="mermaid">{src}</div>',
                        }
                    ]
                },
            },
            syntax_theme="monokai",
            enable_toc=True,
            toc_depth=3,
            enable_math=True,
            enable_mermaid=True,
            enable_emoji=True,
        )


@dataclass
class ServerConfig:
    """Configuration for web server."""

    host: str = "127.0.0.1"
    port: int = 8000
    serve_path: Path = Path(".")
    theme: str = "light"
    open_browser: bool = True
    reload_enabled: bool = True
    allow_write: bool = False
    log_level: str = "INFO"
    telemetry_enabled: bool = True

    def validate(self) -> None:
        """Validate configuration values."""
        if not (1024 <= self.port <= 65535):
            raise ValueError("Port must be 1024-65535")
        if not self.serve_path.exists():
            raise ValueError(f"Path does not exist: {self.serve_path}")
        if self.theme not in VALID_THEMES:
            raise ValueError(f"Invalid theme: {self.theme}")


@dataclass
class WatcherEvent:
    """Represents a file system event from the watcher."""

    event_type: str
    file_path: Path
    timestamp: float

    def is_markdown_file(self) -> bool:
        """Check if event is for a Markdown file."""
        return self.file_path.suffix.lower() in (".md", ".markdown")

    def should_trigger_reload(self) -> bool:
        """Determine if event should trigger browser reload."""
        # Only reload for Markdown files or template/static changes
        return self.is_markdown_file() or any(
            part in self.file_path.parts for part in ("templates", "static")
        )


@dataclass
class WebSocketConnection:
    """Represents an active WebSocket connection for live reload."""

    client_id: str
    websocket: Any
    watched_paths: set[Path] = field(default_factory=set)
    last_ping: float = 0.0

    async def send_reload(self, path: Path | None = None) -> None:
        """Send reload message to client."""
        try:
            await self.websocket.send_json(
                {
                    "type": "reload",
                    "path": str(path) if path else None,
                }
            )
        except Exception:
            pass

    async def send_error(self, message: str) -> None:
        """Send error message to client."""
        try:
            await self.websocket.send_json(
                {
                    "type": "error",
                    "message": message,
                }
            )
        except Exception:
            pass


@dataclass
class ExportConfig:
    """Configuration for static HTML export."""

    source_path: Path
    output_dir: Path
    theme: str = "light"
    use_cdn: bool = True
    minify_html: bool = False

    def validate(self) -> None:
        """Validate export configuration."""
        if not self.source_path.exists():
            raise ValueError(f"Source path does not exist: {self.source_path}")
        if self.theme not in VALID_THEMES:
            raise ValueError(f"Invalid theme: {self.theme}")
