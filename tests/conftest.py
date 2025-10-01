"""Pytest configuration and shared fixtures."""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_markdown_content() -> str:
    """Sample markdown content for testing."""
    return """# Test Document

This is a test document with **bold** and *italic* text.

## Code Block

```python
def hello():
    print("Hello, World!")
```

## Table

| Column 1 | Column 2 |
|----------|----------|
| Value 1  | Value 2  |

## Task List

- [x] Completed task
- [ ] Incomplete task
"""


@pytest.fixture
def tmp_markdown_file(tmp_path: Path, test_markdown_content: str) -> Path:
    """Create a temporary markdown file for testing."""
    file_path = tmp_path / "test.md"
    file_path.write_text(test_markdown_content)
    return file_path


@pytest.fixture
def tmp_markdown_directory(tmp_path: Path, test_markdown_content: str) -> Path:
    """Create a temporary directory with multiple markdown files."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    (docs_dir / "index.md").write_text("# Index\n\nWelcome to the docs!")
    (docs_dir / "quickstart.md").write_text(test_markdown_content)
    (docs_dir / "guide.md").write_text("# Guide\n\nDetailed guide here.")

    # Create subdirectory
    subdir = docs_dir / "advanced"
    subdir.mkdir()
    (subdir / "nested.md").write_text("# Nested\n\nAdvanced topics.")

    return docs_dir


@pytest.fixture
def test_client_single_file(
    tmp_markdown_file: Path,
) -> Generator[TestClient, None, None]:
    """Create TestClient for single file mode."""
    # This will fail until server implementation exists
    try:
        from markdpy.config.models import ServerConfig
        from markdpy.server.app import create_app

        config = ServerConfig(
            host="127.0.0.1",
            port=8000,
            serve_path=tmp_markdown_file,
            theme="light",
            open_browser=False,
            reload_enabled=True,
            allow_write=False,
            log_level="ERROR",
        )

        app = create_app(config)
        with TestClient(app) as client:
            yield client
    except ImportError:
        pytest.skip("Server implementation not available yet")


@pytest.fixture
def test_client_directory(
    tmp_markdown_directory: Path,
) -> Generator[TestClient, None, None]:
    """Create TestClient for directory mode."""
    try:
        from markdpy.config.models import ServerConfig
        from markdpy.server.app import create_app

        config = ServerConfig(
            host="127.0.0.1",
            port=8000,
            serve_path=tmp_markdown_directory,
            theme="light",
            open_browser=False,
            reload_enabled=True,
            allow_write=False,
            log_level="ERROR",
        )

        app = create_app(config)
        with TestClient(app) as client:
            yield client
    except ImportError:
        pytest.skip("Server implementation not available yet")
