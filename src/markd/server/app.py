"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from markd.config.models import ServerConfig, WatcherEvent
from markd.renderer import MarkdownRenderer
from markd.security.path_validator import SecurityError, validate_path
from markd.server.websocket import ConnectionManager, websocket_endpoint
from markd.watcher import FileObserver

logger = logging.getLogger(__name__)


def _handle_file_change(app: FastAPI, event: WatcherEvent) -> None:
    """Handle file system change events by notifying WebSocket clients.

    Args:
        app: FastAPI application instance
        event: File system event
    """
    import asyncio

    logger.debug(f"File change detected: {event.file_path} (type: {event.event_type})")

    if event.should_trigger_reload():
        logger.info(f"Should trigger reload for: {event.file_path}")

        # Broadcast reload to all connected clients
        # Use the event loop stored during lifespan startup
        manager: ConnectionManager = app.state.ws_manager
        loop = getattr(app.state, 'event_loop', None)

        logger.debug(f"Event loop exists: {loop is not None}, WebSocket connections: {manager.get_connection_count()}")

        if loop and loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    manager.send_reload(event.file_path),
                    loop
                )
                # Wait briefly to ensure it's scheduled
                future.result(timeout=0.5)
                logger.info(f"✓ Triggered reload for: {event.file_path}")
            except Exception as e:
                logger.error(f"✗ Failed to trigger reload: {e}")
        else:
            logger.warning(f"Cannot trigger reload - event loop unavailable or not running")


def create_app(config: ServerConfig) -> FastAPI:
    """
    Create and configure FastAPI application.

    Args:
        config: Server configuration

    Returns:
        Configured FastAPI app
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Handle application lifespan events."""
        import asyncio

        # Startup: store event loop and start file watcher
        app.state.event_loop = asyncio.get_running_loop()

        if app.state.file_observer:
            app.state.file_observer.start()

        yield

        # Shutdown: stop file watcher
        if app.state.file_observer:
            app.state.file_observer.stop()

    app = FastAPI(
        title="markd",
        description="Python based Markdown preview server with live reload",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Store config on app state
    app.state.config = config
    # Pass base_path to renderer for link processing
    base_path = config.serve_path if config.serve_path.is_dir() else config.serve_path.parent
    app.state.renderer = MarkdownRenderer(base_path=base_path)
    app.state.ws_manager = ConnectionManager()
    app.state.file_observer = None

    # Setup file watcher if reload enabled
    if config.reload_enabled:
        observer = FileObserver(
            watch_path=config.serve_path if config.serve_path.is_dir() else config.serve_path.parent,
            callback=lambda event: _handle_file_change(app, event),
            debounce_ms=150,
            recursive=True,
        )
        app.state.file_observer = observer

    # Setup templates (now in root directory)
    templates_dir = Path(__file__).parent.parent.parent.parent / "templates"
    app.state.templates = Jinja2Templates(directory=str(templates_dir))

    # Mount static files (now in root directory)
    static_dir = Path(__file__).parent.parent.parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Add security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):  # type: ignore
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        
        # Relaxed CSP for /api/docs (Swagger UI) and /openapi.json
        if request.url.path.startswith("/api/docs") or request.url.path == "/openapi.json":
            response.headers[
                "Content-Security-Policy"
            ] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; img-src 'self' data: https:; font-src 'self' data: https://cdn.jsdelivr.net https://unpkg.com"
        else:
            # Stricter CSP for regular content (allow external images for badges)
            response.headers[
                "Content-Security-Policy"
            ] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' data:"

        # Add cache headers based on content type
        if request.url.path.startswith("/static/"):
            # Static assets: cache for 1 year
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif "text/html" in response.headers.get("content-type", ""):
            # HTML pages: no cache (always fresh)
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response

    # WebSocket endpoint for live reload
    @app.websocket("/ws")
    async def websocket_route(websocket: WebSocket) -> None:
        """WebSocket endpoint for live reload notifications."""
        await websocket_endpoint(websocket, app.state.ws_manager)

    # Root endpoint
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request) -> str:
        """Serve the main page."""
        serve_path = app.state.config.serve_path
        templates = app.state.templates

        if serve_path.is_file():
            # Single file mode
            content = serve_path.read_text(encoding="utf-8")
            rendered_html = app.state.renderer.render(content)

            return templates.TemplateResponse(
                request=request,
                name="single.html",
                context={
                    "filename": serve_path.name,
                    "content": rendered_html,
                    "show_back_link": False,
                    "reload_enabled": app.state.config.reload_enabled,
                    "theme": app.state.config.theme,
                },
            ).body.decode("utf-8")
        else:
            # Directory mode - find index.md or first .md file
            md_files = sorted(serve_path.glob("*.md"))
            if not md_files:
                return templates.TemplateResponse(
                    request=request,
                    name="error.html",
                    context={
                        "status_code": 404,
                        "message": "No Markdown Files Found",
                        "detail": "This directory doesn't contain any Markdown files.",
                        "show_back": False,
                        "reload_enabled": False,
                        "theme": app.state.config.theme,
                    },
                ).body.decode("utf-8")

            # Prefer index.md or README.md
            index_file = None
            for name in ["index.md", "README.md", "readme.md"]:
                candidate = serve_path / name
                if candidate.exists():
                    index_file = candidate
                    break

            file_to_show = index_file or md_files[0]
            content = file_to_show.read_text(encoding="utf-8")
            rendered_html = app.state.renderer.render(content)

            # Build file list for sidebar
            files = [{"name": f.name, "path": f.name} for f in md_files]
            directories = []  # Could scan subdirectories here

            return templates.TemplateResponse(
                request=request,
                name="directory.html",
                context={
                    "content": rendered_html,
                    "files": files,
                    "directories": directories,
                    "current_file": file_to_show.name,
                    "reload_enabled": app.state.config.reload_enabled,
                    "theme": app.state.config.theme,
                },
            ).body.decode("utf-8")

    # View specific file endpoint
    @app.get("/view/{file_path:path}", response_class=HTMLResponse)
    async def view_file(request: Request, file_path: str) -> Response:
        """View a specific Markdown file."""
        serve_path = app.state.config.serve_path
        templates = app.state.templates
        
        # For validation, use parent directory if serving a single file
        # This allows accessing sibling files like LICENSE.md when serving README.md
        validation_root = serve_path if serve_path.is_dir() else serve_path.parent

        try:
            # Validate path security
            requested = Path(file_path)
            abs_path = validate_path(requested, validation_root)

            # Check if file exists
            if not abs_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # For markdown files, render normally
            if abs_path.suffix.lower() in (".md", ".markdown"):
                content = abs_path.read_text(encoding="utf-8")
                rendered_html = app.state.renderer.render(content)
            # For text files (LICENSE, README without extension, .txt), wrap in code block
            elif abs_path.suffix.lower() in (".txt", "") or abs_path.name in ("LICENSE", "README", "CHANGELOG"):
                content = abs_path.read_text(encoding="utf-8")
                # Render as preformatted text
                rendered_html = f'<pre style="white-space: pre-wrap; font-family: monospace; background: var(--code-bg); padding: 20px; border-radius: 6px; overflow-x: auto;">{content}</pre>'
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")

            # (rendered_html is now set by one of the branches above)

            # If serving a directory, show with sidebar; otherwise show single file
            if serve_path.is_dir():
                # Build file list for sidebar
                md_files = sorted(serve_path.glob("*.md"))
                files = [{"name": f.name, "path": f.name} for f in md_files]
                directories = []  # Could scan subdirectories here

                return templates.TemplateResponse(
                    request=request,
                    name="directory.html",
                    context={
                        "content": rendered_html,
                        "files": files,
                        "directories": directories,
                        "current_file": abs_path.name,
                        "reload_enabled": app.state.config.reload_enabled,
                        "theme": app.state.config.theme,
                    },
                )
            else:
                return templates.TemplateResponse(
                    request=request,
                    name="single.html",
                    context={
                        "filename": abs_path.name,
                        "content": rendered_html,
                        "show_back_link": True,
                        "reload_enabled": app.state.config.reload_enabled,
                        "theme": app.state.config.theme,
                    },
                )

        except SecurityError:
            return templates.TemplateResponse(
                request=request,
                name="error.html",
                context={
                    "status_code": 403,
                    "message": "Access Forbidden",
                    "detail": "You don't have permission to access this file.",
                    "show_back": True,
                    "reload_enabled": False,
                    "theme": app.state.config.theme,
                },
                status_code=403,
            )
        except FileNotFoundError:
            return templates.TemplateResponse(
                request=request,
                name="error.html",
                context={
                    "status_code": 404,
                    "message": "File Not Found",
                    "detail": f"The file '{file_path}' doesn't exist.",
                    "show_back": True,
                    "reload_enabled": False,
                    "theme": app.state.config.theme,
                },
                status_code=404,
            )
        except Exception as e:
            return templates.TemplateResponse(
                request=request,
                name="error.html",
                context={
                    "status_code": 500,
                    "message": "Internal Server Error",
                    "detail": str(e),
                    "show_back": True,
                    "reload_enabled": False,
                    "theme": app.state.config.theme,
                },
                status_code=500,
            )

    # Raw endpoint: get raw markdown content (single file mode only)
    @app.get("/raw", response_class=Response)
    async def get_raw_content_single() -> Response:
        """Get raw markdown content of the served file (single file mode only)."""
        serve_path = app.state.config.serve_path
        
        # Only allow /raw endpoint when serving a single file
        if serve_path.is_dir():
            raise HTTPException(
                status_code=403, 
                detail="/raw endpoint is only available when serving a single file"
            )
        
        # Only allow markdown files for /raw endpoint
        if serve_path.suffix.lower() not in (".md", ".markdown"):
            raise HTTPException(
                status_code=400, 
                detail="Only markdown files (.md, .markdown) are supported by /raw endpoint"
            )

        try:
            # Read and return raw content of the served file
            content = serve_path.read_text(encoding="utf-8")
            return Response(
                content=content,
                media_type="text/plain; charset=utf-8",
                headers={
                    "Content-Disposition": f'inline; filename="{serve_path.name}"',
                    "X-Content-Type-Options": "nosniff",
                }
            )

        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Raw endpoint with path: get raw markdown content (single file mode only)
    @app.get("/raw/{file_path:path}", response_class=Response)
    async def get_raw_content(file_path: str) -> Response:
        """Get raw markdown content without rendering (single file mode only)."""
        serve_path = app.state.config.serve_path
        
        # Only allow /raw endpoint when serving a single file
        if serve_path.is_dir():
            raise HTTPException(
                status_code=403, 
                detail="/raw endpoint is only available when serving a single file"
            )
        
        # For validation, use parent directory since we're serving a single file
        validation_root = serve_path.parent

        try:
            # Validate path security
            requested = Path(file_path)
            abs_path = validate_path(requested, validation_root)

            # Check if file exists
            if not abs_path.exists():
                raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

            # Only allow markdown files for /raw endpoint
            if abs_path.suffix.lower() not in (".md", ".markdown"):
                raise HTTPException(
                    status_code=400, 
                    detail="Only markdown files (.md, .markdown) are supported by /raw endpoint"
                )

            # Read and return raw content
            content = abs_path.read_text(encoding="utf-8")
            return Response(
                content=content,
                media_type="text/plain; charset=utf-8",
                headers={
                    "Content-Disposition": f'inline; filename="{abs_path.name}"',
                    "X-Content-Type-Options": "nosniff",
                }
            )

        except SecurityError:
            raise HTTPException(status_code=403, detail="Access forbidden")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")

    # API endpoint: get file tree
    @app.get("/api/files")
    async def api_files() -> dict:
        """Get directory tree structure as JSON."""
        serve_path = app.state.config.serve_path

        if serve_path.is_file():
            raise HTTPException(status_code=404, detail="Not available in single file mode")

        def build_tree(directory: Path) -> dict:
            """Recursively build directory tree."""
            files = []
            subdirs = []

            for item in sorted(directory.iterdir()):
                if item.is_file() and item.suffix.lower() in (".md", ".markdown"):
                    stat = item.stat()
                    files.append({
                        "name": item.name,
                        "path": str(item.relative_to(serve_path)),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    })
                elif item.is_dir() and not item.name.startswith("."):
                    child_tree = build_tree(item)
                    subdirs.append({
                        "name": item.name,
                        "path": str(item.relative_to(serve_path)),
                        "files": child_tree["files"],
                        "subdirs": child_tree["subdirs"],
                    })

            return {"files": files, "subdirs": subdirs}

        tree_data = build_tree(serve_path)

        return {
            "root": str(serve_path),
            "files": tree_data["files"],
            "tree": {
                "name": serve_path.name,
                "path": ".",
                "files": tree_data["files"],
                "subdirs": tree_data["subdirs"],
            }
        }

    # API endpoint: get file metadata
    @app.get("/api/file/{file_path:path}")
    async def api_file_metadata(file_path: str) -> dict:
        """Get metadata for a specific file."""
        serve_path = app.state.config.serve_path
        # Use parent directory if serving a single file
        validation_root = serve_path if serve_path.is_dir() else serve_path.parent

        try:
            requested = Path(file_path)
            abs_path = validate_path(requested, validation_root)

            if not abs_path.is_file():
                raise HTTPException(status_code=404, detail="File not found")

            stat = abs_path.stat()
            content = abs_path.read_text(encoding="utf-8")

            return {
                "path": str(abs_path.relative_to(validation_root)),
                "name": abs_path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "content_hash": hash(content),
                "is_markdown": abs_path.suffix.lower() in (".md", ".markdown"),
            }

        except SecurityError:
            raise HTTPException(status_code=403, detail="Access forbidden")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")

    return app
