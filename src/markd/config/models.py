"""Core data models for markd."""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Valid theme names
VALID_THEMES = ["light", "dark", "catppuccin-mocha", "catppuccin-latte"]


@dataclass
class MarkdownFile:
    """Represents a Markdown file in the file system."""

    path: Path  # Absolute path to file
    relative_path: Path  # Path relative to serve root
    content: str  # Raw Markdown content
    content_hash: str  # SHA256 hash for caching
    rendered_html: str | None = None  # Cached rendered HTML
    metadata: dict[str, Any] = field(default_factory=dict)  # Frontmatter metadata
    modified_time: float = 0.0  # Last modification timestamp
    file_size: int = 0  # Size in bytes

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

    path: Path  # Absolute directory path
    relative_path: Path  # Path relative to serve root
    files: list[MarkdownFile] = field(default_factory=list)  # Markdown files in directory
    subdirectories: list["DirectoryListing"] = field(
        default_factory=list
    )  # Nested directories
    index_file: MarkdownFile | None = None  # index.md or README.md if present

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

    extensions: list[str] = field(default_factory=list)  # Markdown extensions to enable
    extension_configs: dict[str, Any] = field(
        default_factory=dict
    )  # Extension-specific settings
    syntax_theme: str = "monokai"  # Pygments theme name
    enable_toc: bool = True  # Generate table of contents
    toc_depth: int = 3  # Max heading level for TOC (1-6)
    enable_math: bool = True  # Enable MathJax rendering
    enable_mermaid: bool = True  # Enable Mermaid diagrams
    enable_emoji: bool = True  # Enable emoji shortcodes

    @classmethod
    def default(cls) -> "RenderConfig":
      """Create default configuration with rich Markdown + pymdownx support."""
      return cls(
        extensions = [
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

        extension_configs = {
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
                        "format": lambda src, *args, **kwargs: f'<div class="mermaid">{src}</div>',
                    }
                ]
            }
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

    host: str = "127.0.0.1"  # Bind address
    port: int = 8000  # Port number
    serve_path: Path = Path(".")  # Root directory or file to serve
    theme: str = "light"  # UI theme name
    open_browser: bool = True  # Auto-open browser on start
    reload_enabled: bool = True  # Enable live reload
    allow_write: bool = False  # Allow write operations
    log_level: str = "INFO"  # Logging level

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

    event_type: str  # created, modified, deleted, moved
    file_path: Path  # Absolute path to affected file
    timestamp: float  # Event timestamp

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

    client_id: str  # Unique client identifier
    websocket: Any  # WebSocket instance (FastAPI WebSocket)
    watched_paths: set[Path] = field(default_factory=set)  # Files client is watching
    last_ping: float = 0.0  # Last ping timestamp

    async def send_reload(self, path: Path | None = None) -> None:
        """Send reload message to client."""
        try:
            await self.websocket.send_json({
                "type": "reload",
                "path": str(path) if path else None,
            })
        except Exception:
            pass  # Connection may be closed

    async def send_error(self, message: str) -> None:
        """Send error message to client."""
        try:
            await self.websocket.send_json({
                "type": "error",
                "message": message,
            })
        except Exception:
            pass  # Connection may be closed


@dataclass
class ExportConfig:
    """Configuration for static HTML export."""

    source_path: Path  # Source file or directory
    output_dir: Path  # Output directory for exported files
    theme: str = "light"  # Theme to use for export
    use_cdn: bool = True  # Use CDN for libraries (MathJax, Mermaid)
    minify_html: bool = False  # Minify exported HTML

    def validate(self) -> None:
        """Validate export configuration."""
        if not self.source_path.exists():
            raise ValueError(f"Source path does not exist: {self.source_path}")
        if self.theme not in VALID_THEMES:
            raise ValueError(f"Invalid theme: {self.theme}")
