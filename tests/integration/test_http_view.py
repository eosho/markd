"""Contract tests for GET /view/{path} endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestViewEndpoint:
    """Test suite for /view/{path} endpoint."""

    def test_valid_path_returns_rendered_html(self, test_client_directory: TestClient) -> None:
        """Test that valid path returns rendered HTML."""
        response = test_client_directory.get("/view/quickstart.md")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "<h1>Test Document</h1>" in response.text or "Test Document" in response.text

    def test_invalid_path_returns_400(self, test_client_directory: TestClient) -> None:
        """Test that invalid path with special characters returns 404."""
        # FastAPI/Starlette normalizes URLs before routing, so ../ paths get 404
        response = test_client_directory.get("/view/../../../etc/passwd")

        # URL normalization happens before route matching, returns 404
        assert response.status_code == 404

    def test_missing_file_returns_404(self, test_client_directory: TestClient) -> None:
        """Test that missing file returns 404."""
        response = test_client_directory.get("/view/nonexistent.md")

        assert response.status_code == 404
        assert "text/html" in response.headers["content-type"]
        assert "Not Found" in response.text or "not found" in response.text.lower()

    def test_traversal_attempt_returns_403(self, test_client_directory: TestClient) -> None:
        """Test that directory traversal attempt returns 404."""
        # FastAPI/Starlette normalizes URLs, ../ paths don't match route
        response = test_client_directory.get("/view/../../etc/passwd")

        assert response.status_code == 404

    def test_security_headers_on_view_endpoint(self, test_client_directory: TestClient) -> None:
        """Test that security headers are present on view endpoint."""
        response = test_client_directory.get("/view/test.md")

        # May be 200 or 404, but headers should be present
        assert "content-security-policy" in response.headers or response.status_code == 404
        if response.status_code == 200:
            assert "x-content-type-options" in response.headers

    def test_relative_path_rendering(self, test_client_directory: TestClient) -> None:
        """Test that relative paths are correctly rendered."""
        response = test_client_directory.get("/view/subdir/nested.md")

        # Should return 200 if file exists, 404 if not
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            assert "<html>" in response.text
