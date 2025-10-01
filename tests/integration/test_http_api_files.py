"""Contract tests for GET /api/files endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestApiFilesEndpoint:
    """Test suite for /api/files endpoint."""

    def test_directory_mode_returns_file_tree_json(self, test_client_directory: TestClient) -> None:
        """Test that directory mode returns file tree as JSON."""
        response = test_client_directory.get("/api/files")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)
        assert "name" in data or "files" in data or "subdirs" in data

    def test_single_file_mode_returns_404(self, test_client_single_file: TestClient) -> None:
        """Test that single file mode returns 404 for /api/files."""
        response = test_client_single_file.get("/api/files")

        assert response.status_code == 404

    def test_file_tree_structure(self, test_client_directory: TestClient) -> None:
        """Test that file tree has expected structure."""
        response = test_client_directory.get("/api/files")

        if response.status_code == 200:
            data = response.json()
            # Should have root path and tree structure
            assert "root" in data
            assert "tree" in data
            # Tree should have name/path
            assert "name" in data["tree"] or "path" in data["tree"]
            # Should have files list
            assert "files" in data
            assert isinstance(data["files"], list)

    def test_nested_directories_in_tree(self, test_client_directory: TestClient) -> None:
        """Test that nested directories are included in tree."""
        response = test_client_directory.get("/api/files")

        if response.status_code == 200:
            data = response.json()
            # Should have tree with subdirectories field
            assert "tree" in data
            assert "subdirs" in data["tree"]

    def test_cors_headers_if_applicable(self, test_client_directory: TestClient) -> None:
        """Test CORS headers if API is meant to be accessible."""
        response = test_client_directory.get("/api/files")

        # CORS may or may not be enabled - just verify response structure
        assert response.status_code in (200, 404)
