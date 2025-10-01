"""FastAPI middleware for security headers and caching.

This module provides middleware that adds:
- Security headers (CSP, X-Content-Type-Options, X-Frame-Options)
- Caching headers for static assets and HTML pages
"""

from fastapi import Request, Response


async def add_security_headers(request: Request, call_next) -> Response:  # type: ignore
    """Add security and caching headers to responses.

    Security headers:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - Content-Security-Policy: Varies by endpoint

    Caching headers:
    - Static assets: Cache for 1 year (immutable)
    - HTML pages: No cache (always fresh)

    Args:
        request: Incoming request
        call_next: Next middleware/handler

    Returns:
        Response with added headers
    """
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"

    # Content Security Policy
    if request.url.path.startswith("/api/docs") or request.url.path == "/openapi.json":
        # Relaxed CSP for Swagger UI
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https://cdn.jsdelivr.net https://unpkg.com"
        )
    else:
        # Stricter CSP for regular content (allow external images for badges)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:"
        )

    # Caching headers
    if request.url.path.startswith("/static/"):
        # Static assets: cache for 1 year (immutable)
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif "text/html" in response.headers.get("content-type", ""):
        # HTML pages: no cache (always fresh for live reload)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response
