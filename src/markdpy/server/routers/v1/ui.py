"""UI router for HTML page rendering.

This router handles all HTML page rendering endpoints including
the root page, file viewing, and error pages.
"""

import logging
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from markdpy.config.models import ServerConfig
from markdpy.renderer import MarkdownRenderer
from markdpy.security.path_validator import SecurityError, validate_path
from markdpy.server.dependencies import (
    get_config,
    get_reload_enabled,
    get_renderer,
    get_serve_path,
    get_templates,
    get_theme,
    get_validation_root,
)
from markdpy.telemetry import track_error, track_render

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ui"])


@router.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    config: ServerConfig = Depends(get_config),
    renderer: MarkdownRenderer = Depends(get_renderer),
    templates: Jinja2Templates = Depends(get_templates),
    theme: str = Depends(get_theme),
    reload_enabled: bool = Depends(get_reload_enabled),
) -> HTMLResponse:
    """Serve the main page.

    In single file mode, renders the served file.
    In directory mode, finds and renders index.md or first .md file.

    Args:
        request: FastAPI request object
        config: Server configuration (injected)
        renderer: Markdown renderer (injected)
        templates: Jinja2 templates (injected)
        theme: Current theme (injected)
        reload_enabled: Live reload status (injected)

    Returns:
        Rendered HTML page
    """
    start_time = time.time()
    serve_path = config.serve_path

    try:
        if serve_path.is_file():
            # Single file mode
            content = serve_path.read_text(encoding="utf-8")
            rendered_html = renderer.render(content)

            response = templates.TemplateResponse(
                request=request,
                name="single.html",
                context={
                    "filename": serve_path.name,
                    "content": rendered_html,
                    "show_back_link": False,
                    "reload_enabled": reload_enabled,
                    "theme": theme,
                },
            )

            # Track successful render
            render_time_ms = (time.time() - start_time) * 1000
            track_render(render_time_ms)
            return response

        # Directory mode - find index.md or first .md file
        md_files = sorted(serve_path.glob("*.md"))
        if not md_files:
            track_error()  # Track error for no markdown files
            return templates.TemplateResponse(
                request=request,
                name="error.html",
                context={
                    "status_code": 404,
                    "message": "No Markdown Files Found",
                    "detail": "This directory doesn't contain any Markdown files.",
                    "show_back": False,
                    "reload_enabled": False,
                    "theme": theme,
                },
            )

        # Prefer index.md or README.md
        index_file = None
        for name in ["index.md", "README.md", "readme.md"]:
            candidate = serve_path / name
            if candidate.exists():
                index_file = candidate
                break

        file_to_show = index_file or md_files[0]
        content = file_to_show.read_text(encoding="utf-8")
        rendered_html = renderer.render(content)

        # Build file list for sidebar
        files = [{"name": f.name, "path": f.name} for f in md_files]
        directories = []  # Could scan subdirectories here

        response = templates.TemplateResponse(
            request=request,
            name="directory.html",
            context={
                "content": rendered_html,
                "files": files,
                "directories": directories,
                "current_file": file_to_show.name,
                "reload_enabled": reload_enabled,
                "theme": theme,
            },
        )

        # Track successful render
        render_time_ms = (time.time() - start_time) * 1000
        track_render(render_time_ms)
        return response

    except Exception:
        try:
            track_error()  # Track any unexpected errors
        except Exception:
            logger.exception("track_error() failed in root endpoint")
        logger.exception("Error in root endpoint")
        raise


@router.get("/view/{file_path:path}", response_class=HTMLResponse)
async def view_file(
    request: Request,
    file_path: str,
    serve_path: Path = Depends(get_serve_path),
    validation_root: Path = Depends(get_validation_root),
    renderer: MarkdownRenderer = Depends(get_renderer),
    templates: Jinja2Templates = Depends(get_templates),
    theme: str = Depends(get_theme),
    reload_enabled: bool = Depends(get_reload_enabled),
) -> HTMLResponse:
    """View a specific Markdown file.

    Args:
        request: FastAPI request object
        file_path: Relative path to file to view
        serve_path: Path being served (injected)
        validation_root: Root path for validation (injected)
        renderer: Markdown renderer (injected)
        templates: Jinja2 templates (injected)
        theme: Current theme (injected)
        reload_enabled: Live reload status (injected)

    Returns:
        Rendered HTML page or error page

    Raises:
        HTTPException: If file access is denied or not found
    """
    start_time = time.time()

    try:
        # Validate path security
        requested = Path(file_path)
        abs_path = validate_path(requested, validation_root)

        # File existence check is performed inside validate_path

        # For markdown files, render normally
        if abs_path.suffix.lower() in (".md", ".markdown"):
            content = abs_path.read_text(encoding="utf-8")
            rendered_html = renderer.render(content)
        # For text files (LICENSE, README without extension, .txt), wrap in code block
        elif abs_path.suffix.lower() in (".txt", "") or abs_path.name in (
            "LICENSE",
            "README",
            "CHANGELOG",
        ):
            content = abs_path.read_text(encoding="utf-8")
            # Render as preformatted text
            rendered_html = (
                f'<pre style="white-space: pre-wrap; font-family: monospace; '
                f"background: var(--code-bg); padding: 20px; border-radius: 6px; "
                f'overflow-x: auto;">{content}</pre>'
            )
        else:
            track_error()  # Track unsupported file type error
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # If serving a directory, show with sidebar; otherwise show single file
        if serve_path.is_dir():
            # Build file list for sidebar
            md_files = sorted(serve_path.glob("*.md"))
            files = [{"name": f.name, "path": f.name} for f in md_files]
            directories = []  # Could scan subdirectories here

            response = templates.TemplateResponse(
                request=request,
                name="directory.html",
                context={
                    "content": rendered_html,
                    "files": files,
                    "directories": directories,
                    "current_file": abs_path.name,
                    "reload_enabled": reload_enabled,
                    "theme": theme,
                },
            )
        else:
            response = templates.TemplateResponse(
                request=request,
                name="single.html",
                context={
                    "filename": abs_path.name,
                    "content": rendered_html,
                    "show_back_link": True,
                    "reload_enabled": reload_enabled,
                    "theme": theme,
                },
            )

        # Track successful render
        render_time_ms = (time.time() - start_time) * 1000
        track_render(render_time_ms)
        return response

    except SecurityError:
        track_error()  # Track security error
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "status_code": 403,
                "message": "Access Forbidden",
                "detail": "You don't have permission to access this file.",
                "show_back": True,
                "reload_enabled": False,
                "theme": theme,
            },
            status_code=403,
        )
    except FileNotFoundError:
        track_error()  # Track file not found error
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "status_code": 404,
                "message": "File Not Found",
                "detail": f"The file '{file_path}' doesn't exist.",
                "show_back": True,
                "reload_enabled": False,
                "theme": theme,
            },
            status_code=404,
        )
    except Exception as e:
        track_error()  # Track any other errors
        logger.exception(f"Error viewing file {file_path}")
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "status_code": 500,
                "message": "Internal Server Error",
                "detail": str(e),
                "show_back": True,
                "reload_enabled": False,
                "theme": theme,
            },
            status_code=500,
        )


@router.get("/raw", response_class=Response)
async def get_raw_content_single(
    serve_path: Path = Depends(get_serve_path),
) -> Response:
    """Get raw markdown content of the served file (single file mode only).

    Args:
        serve_path: Path being served (injected)

    Returns:
        Raw markdown content as text/plain

    Raises:
        HTTPException: If not in single file mode or file not found
    """
    # Only allow /raw endpoint when serving a single file
    if serve_path.is_dir():
        raise HTTPException(
            status_code=403, detail="/raw endpoint is only available when serving a single file"
        )

    # Only allow markdown files for /raw endpoint
    if serve_path.suffix.lower() not in (".md", ".markdown"):
        raise HTTPException(
            status_code=400,
            detail="Only markdown files (.md, .markdown) are supported by /raw endpoint",
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
            },
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.exception("Error getting raw content")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/raw/{file_path:path}", response_class=Response)
async def get_raw_content(
    file_path: str,
    serve_path: Path = Depends(get_serve_path),
    validation_root: Path = Depends(get_validation_root),
) -> Response:
    """Get raw markdown content without rendering (single file mode only).

    Args:
        file_path: Relative path to file
        serve_path: Path being served (injected)
        validation_root: Root path for validation (injected)

    Returns:
        Raw markdown content as text/plain

    Raises:
        HTTPException: If not in single file mode, file not found, or access denied
    """
    # Only allow /raw endpoint when serving a single file
    if serve_path.is_dir():
        raise HTTPException(
            status_code=403, detail="/raw endpoint is only available when serving a single file"
        )

    try:
        # Validate path security
        abs_path = validate_path(file_path, validation_root)

        # Check if file exists and is a regular file (not symlink/directory/etc)
        if not abs_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        if not abs_path.is_file():
            raise HTTPException(status_code=404, detail=f"Path is not a regular file: {file_path}")
        if abs_path.is_symlink():
            raise HTTPException(status_code=403, detail="Symlinks are not allowed")

        # Only allow markdown files for /raw endpoint
        if abs_path.suffix.lower() not in (".md", ".markdown"):
            raise HTTPException(
                status_code=400,
                detail="Only markdown files (.md, .markdown) are supported by /raw endpoint",
            )

        # Read and return raw content
        content = abs_path.read_text(encoding="utf-8")
        return Response(
            content=content,
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f'inline; filename="{abs_path.name}"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    except SecurityError:
        raise HTTPException(status_code=403, detail="Access forbidden")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.exception(f"Error getting raw content for {file_path}")
        raise HTTPException(status_code=500, detail=str(e))
