"""API router for JSON endpoints.

This router handles all JSON API endpoints including file tree listing,
file metadata, and raw markdown content.
"""

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from markd.security.path_validator import SecurityError, validate_path
from markd.server.dependencies import get_serve_path, get_validation_root

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/files")
async def api_files(
    serve_path: Path = Depends(get_serve_path),
) -> dict[str, Any]:
    """Get directory tree structure as JSON.

    Only available in directory mode.

    Args:
        serve_path: Path being served (injected)

    Returns:
        Directory tree structure with files and subdirectories

    Raises:
        HTTPException: If in single file mode
    """
    if serve_path.is_file():
        raise HTTPException(status_code=404, detail="Not available in single file mode")

    def build_tree(directory: Path) -> dict[str, Any]:
        """Recursively build directory tree.

        Args:
            directory: Directory to scan

        Returns:
            Dictionary with files and subdirs lists
        """
        files = []
        subdirs = []

        for item in sorted(directory.iterdir()):
            if item.is_file() and item.suffix.lower() in (".md", ".markdown"):
                stat = item.stat()
                files.append(
                    {
                        "name": item.name,
                        "path": str(item.relative_to(serve_path)),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    }
                )
            elif item.is_dir() and not item.name.startswith("."):
                child_tree = build_tree(item)
                subdirs.append(
                    {
                        "name": item.name,
                        "path": str(item.relative_to(serve_path)),
                        "files": child_tree["files"],
                        "subdirs": child_tree["subdirs"],
                    }
                )

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
        },
    }


@router.get("/file/{file_path:path}")
async def api_file_metadata(
    file_path: str,
    validation_root: Path = Depends(get_validation_root),
) -> dict[str, Any]:
    """Get metadata for a specific file.

    Args:
        file_path: Relative path to file
        validation_root: Root path for validation (injected)

    Returns:
        File metadata including path, name, size, modified time, and content hash

    Raises:
        HTTPException: If file is not found or access is denied
    """
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
    except Exception as e:
        logger.exception(f"Error getting metadata for {file_path}")
        raise HTTPException(status_code=500, detail=str(e))


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
        requested = Path(file_path)
        abs_path = validate_path(requested, validation_root)

        # Check if file exists
        if not abs_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

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
