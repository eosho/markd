"""Path validation for security."""

from pathlib import Path


class SecurityError(Exception):
    """Raised when a security validation fails."""

    pass


def validate_path(requested_path: Path, root_path: Path) -> Path:
    """
    Validate that requested path is within root directory.

    Prevents directory traversal attacks by ensuring the resolved path
    is relative to the root directory.

    Args:
        requested_path: The path requested by the user
        root_path: The root directory to serve from

    Returns:
        The resolved absolute path if valid

    Raises:
        SecurityError: If path is outside root or invalid
    """
    try:
        # Resolve both paths to absolute (strict=False allows nonexistent paths)
        abs_root = root_path.resolve(strict=False)
        abs_requested = (root_path / requested_path).resolve(strict=False)

        # Check if requested path is relative to root
        if not abs_requested.is_relative_to(abs_root):
            raise SecurityError(f"Access denied: {requested_path} is outside serve root")

        # Check if path exists
        if not abs_requested.exists():
            raise FileNotFoundError(f"Path not found: {requested_path}")

        return abs_requested

    except ValueError as e:
        # ValueError from invalid path operations
        raise SecurityError(f"Invalid path: {requested_path}") from e


def is_safe_path(requested_path: Path, root_path: Path) -> bool:
    """
    Check if path is safe without raising exception.

    Args:
        requested_path: The path to check
        root_path: The root directory

    Returns:
        True if path is safe, False otherwise
    """
    try:
        validate_path(requested_path, root_path)
        return True
    except (SecurityError, FileNotFoundError):
        return False
