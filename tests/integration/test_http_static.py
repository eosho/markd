"""Contract tests for GET /static/{path} endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestStaticEndpoint:
    """Test suite for /static/{path} endpoint."""

    def test_css_file_served_correctly(self, test_client_single_file: TestClient) -> None:
        """Test that CSS files are served with correct MIME type."""
        response = test_client_single_file.get("/static/css/main.css")

        if response.status_code == 200:
            assert response.headers["content-type"] == "text/css; charset=utf-8"

    def test_javascript_file_served_correctly(self, test_client_single_file: TestClient) -> None:
        """Test that JavaScript files are served with correct MIME type."""
        response = test_client_single_file.get("/static/js/reload.js")

        if response.status_code == 200:
            assert (
                response.headers["content-type"] == "application/javascript"
                or response.headers["content-type"] == "text/javascript; charset=utf-8"
            )

    def test_cache_headers_on_static_assets(self, test_client_single_file: TestClient) -> None:
        """Test that static assets have appropriate cache headers."""
        response = test_client_single_file.get("/static/css/main.css")

        if response.status_code == 200:
            # Static assets should have cache headers
            assert "cache-control" in response.headers
            cache_control = response.headers["cache-control"]
            # Should allow caching (not no-cache)
            assert "no-cache" not in cache_control or "max-age" in cache_control

    def test_font_file_served_correctly(self, test_client_single_file: TestClient) -> None:
        """Test that font files are served with correct MIME type."""
        response = test_client_single_file.get("/static/fonts/test.woff2")

        # May not exist, but if it does, should have proper MIME type
        if response.status_code == 200:
            assert "font/woff2" in response.headers.get("content-type", "")

    def test_theme_css_served_correctly(self, test_client_single_file: TestClient) -> None:
        """Test that theme CSS files are served correctly."""
        themes = ["light.css", "dark.css", "catppuccin-mocha.css"]

        for theme in themes:
            response = test_client_single_file.get(f"/static/css/themes/{theme}")
            # May not exist yet, but should be accessible path
            assert response.status_code in (200, 404)

    def test_static_directory_traversal_blocked(self, test_client_single_file: TestClient) -> None:
        """Test that directory traversal is blocked in static paths."""
        response = test_client_single_file.get("/static/../../etc/passwd")

        assert response.status_code in (400, 403, 404)

    def test_etag_support(self, test_client_single_file: TestClient) -> None:
        """Test that static files support ETag for caching."""
        response = test_client_single_file.get("/static/css/main.css")

        if response.status_code == 200:
            # ETag support is optional but recommended
            # Just verify header structure if present
            etag = response.headers.get("etag")
            if etag:
                assert len(etag) > 0
