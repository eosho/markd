"""Contract tests for GET / (root) endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestRootEndpoint:
    """Test suite for root endpoint (/)."""

    def test_single_file_mode_returns_html(self, test_client_single_file: TestClient) -> None:
        """Test that single file mode returns HTML with rendered content."""
        response = test_client_single_file.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "<!DOCTYPE html>" in response.text
        assert '<div class="rendered-content">' in response.text

    def test_single_file_includes_live_reload_script(
        self, test_client_single_file: TestClient
    ) -> None:
        """Test that live reload script is included."""
        response = test_client_single_file.get("/")

        assert response.status_code == 200
        assert '<script src="/static/js/reload.js"></script>' in response.text

    def test_directory_mode_returns_html_with_sidebar(
        self, test_client_directory: TestClient
    ) -> None:
        """Test that directory mode returns HTML with sidebar navigation."""
        response = test_client_directory.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert '<nav class="sidebar">' in response.text
        assert '<div class="rendered-content">' in response.text

    def test_security_headers_present(self, test_client_single_file: TestClient) -> None:
        """Test that security headers are included in response."""
        response = test_client_single_file.get("/")

        assert response.status_code == 200
        assert "content-security-policy" in response.headers
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"

    def test_csp_header_restricts_sources(self, test_client_single_file: TestClient) -> None:
        """Test that CSP header properly restricts script and style sources."""
        response = test_client_single_file.get("/")

        csp = response.headers.get("content-security-policy", "")
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp or "script-src" in csp

    def test_no_cache_header(self, test_client_single_file: TestClient) -> None:
        """Test that cache-control is set to no-cache for dynamic content."""
        response = test_client_single_file.get("/")

        assert response.status_code == 200
        cache_control = response.headers.get("cache-control", "")
        assert "no-cache" in cache_control
        assert "no-store" in cache_control
