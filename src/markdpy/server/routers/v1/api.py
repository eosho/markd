"""API router for JSON endpoints.

This router handles all JSON API endpoints including file tree listing,
file metadata, and raw markdown content.
"""

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from markdpy.security.path_validator import SecurityError, validate_path
from markdpy.server.dependencies import get_serve_path, get_validation_root

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
