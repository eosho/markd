"""Path validation for security."""

import re
from pathlib import Path


class SecurityError(Exception):
    """Raised when a security validation fails."""

    pass


def _is_safe_filename(filename: str) -> bool:
    """Check if filename contains only safe characters.

    Args:
        filename: Filename to check

    Returns:
        True if filename is safe, False otherwise
    """
    # Allow alphanumeric, dash, underscore, dot, and space
    # No directory separators, no control characters
    safe_pattern = re.compile(r"^[a-zA-Z0-9._\-\s]+$")
    return bool(safe_pattern.match(filename))


def _contains_path_traversal(path_str: str) -> bool:
    """Check if path string contains path traversal patterns.

    Args:
        path_str: Path string to check

    Returns:
        True if path contains traversal patterns, False otherwise
    """
    # Check for various path traversal patterns before normalization
    dangerous_patterns = [
        "..",  # Parent directory reference
        "~",  # Home directory reference
        "//",  # Double slashes
        "\\\\",  # Double backslashes
        "/.",  # Hidden files at root
    ]

    for pattern in dangerous_patterns:
        if pattern in path_str:
            return True

    # Check for backslash (Windows separator) - should be caught by filename validation
    if "\\" in path_str:
        return True

    # Check for encoded traversal attempts (case-insensitive)
    path_lower = path_str.lower()
    encoded_patterns = [
        "%2e%2e",  # URL encoded ..
        "%252e%252e",  # Double encoded ..
        "..%2f",  # Mixed encoding
        "%2e%2e/",  # Mixed encoding
        "..%5c",  # Windows separator
        "%2e%2e%5c",  # Windows separator
    ]

    for pattern in encoded_patterns:
        if pattern.lower() in path_lower:
            return True

    return False


def validate_path(requested_path: Path | str, root_path: Path) -> Path:
    """
    Validate that requested path is within root directory with enhanced security.

    Prevents directory traversal attacks by:
    1. Checking for path traversal patterns (../, ~/, etc.)
    2. Validating each path component for safe characters
    3. Ensuring resolved path is within root directory
    4. Preventing access to hidden files and system files

    Args:
        requested_path: The path requested by the user (Path or str)
        root_path: The root directory to serve from

    Returns:
        The resolved absolute path if valid

    Raises:
        SecurityError: If path is outside root or contains invalid patterns
    """
    # Get the original string representation before Path normalization
    if isinstance(requested_path, str):
        requested_path = Path(requested_path)

    # Reject outright if the path is absolute
    if requested_path.is_absolute():
        raise SecurityError(
            f"Absolute path supplied: {requested_path}. "
            "User input must be a relative path within the root directory."
        )

    # Validate each path component
    path_parts = requested_path.parts
    for part in path_parts:
        # Skip empty parts and current directory references
        if not part or part == ".":
            continue

        # Check for hidden files (starting with .)
        if part.startswith("."):
            raise SecurityError(
                f"Access to hidden files denied: {part}. Paths starting with '.' are not allowed."
            )

        # Validate filename characters
        if not _is_safe_filename(part):
            raise SecurityError(
                f"Invalid characters in path component: {part}. "
                "Only alphanumeric characters, dash, underscore, dot, and space are allowed."
            )

        # Check for multiple dots (except for file extensions)
        if part.count(".") > 1:
            # Allow one dot for file extension (e.g., file.md)
            # But disallow multiple dots (e.g., file..md, ...file)
            dots = [i for i, c in enumerate(part) if c == "."]
            # Check if dots are not adjacent
            for i in range(len(dots) - 1):
                if dots[i + 1] - dots[i] <= 1:
                    raise SecurityError(
                        f"Multiple adjacent dots in path component: {part}. "
                        "This pattern is not allowed."
                    )

    try:
        # Resolve both paths to absolute (strict=False allows nonexistent paths)
        abs_root = root_path.resolve(strict=False)
        abs_requested = (root_path / requested_path).resolve(strict=False)

        # Check if requested path is relative to root
        if not abs_requested.is_relative_to(abs_root):
            raise SecurityError(
                f"Access denied: {requested_path} is outside serve root. "
                f"Requested: {abs_requested}, Root: {abs_root}"
            )

        # Additional check: ensure the path doesn't contain symlinks that escape root
        # This is a defense-in-depth measure
        try:
            # Get the real path (follows symlinks)
            if abs_requested.exists():
                real_path = abs_requested.resolve(strict=True)
            else:
                real_path = abs_requested

            if not real_path.is_relative_to(abs_root):
                raise SecurityError(
                    f"Symlink traversal attempt detected: {requested_path} "
                    f"resolves outside serve root."
                )
        except (OSError, RuntimeError) as e:
            # If we can't resolve symlinks, raise a security error
            raise SecurityError(f"Failed to resolve symlinks for {requested_path}: {e}") from e

        # Check if path exists
        if not abs_requested.exists():
            raise FileNotFoundError(f"Path not found: {requested_path}")

        return real_path

    except ValueError as e:
        # ValueError from invalid path operations
        raise SecurityError(f"Invalid path operation: {requested_path}") from e


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
