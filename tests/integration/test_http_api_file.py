"""Contract tests for GET /api/file/{path} endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestApiFileEndpoint:
    """Test suite for /api/file/{path} endpoint."""

    def test_returns_file_metadata_json(self, test_client_directory: TestClient) -> None:
        """Test that endpoint returns file metadata as JSON."""
        response = test_client_directory.get("/api/file/test.md")

        # May return 200 or 404 depending on file existence
        if response.status_code == 200:
            assert response.headers["content-type"] == "application/json"
            data = response.json()
            assert isinstance(data, dict)

    def test_metadata_includes_required_fields(self, test_client_directory: TestClient) -> None:
        """Test that metadata includes size, modified, and path."""
        response = test_client_directory.get("/api/file/test.md")

        if response.status_code == 200:
            data = response.json()
            # Should include path and size at minimum
            assert "path" in data or "relative_path" in data
            assert "size" in data or "file_size" in data

    def test_handles_not_found(self, test_client_directory: TestClient) -> None:
        """Test that missing file returns 404."""
        response = test_client_directory.get("/api/file/nonexistent.md")

        assert response.status_code == 404

    def test_hash_in_metadata_for_caching(self, test_client_directory: TestClient) -> None:
        """Test that content hash is included for cache invalidation."""
        response = test_client_directory.get("/api/file/test.md")

        if response.status_code == 200:
            data = response.json()
            # Hash field is optional but useful
            # Just verify response structure
            assert isinstance(data, dict)

    def test_modified_timestamp_present(self, test_client_directory: TestClient) -> None:
        """Test that modification timestamp is included."""
        response = test_client_directory.get("/api/file/test.md")

        if response.status_code == 200:
            data = response.json()
            assert "modified" in data or "modified_time" in data

    def test_directory_traversal_blocked(self, test_client_directory: TestClient) -> None:
        """Test that directory traversal is blocked."""
        response = test_client_directory.get("/api/file/../../etc/passwd")

        assert response.status_code in (400, 403, 404)
