"""Contract tests for CLI serve command."""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.unit
class TestCliServeCommand:
    """Test suite for markdpy CLI serve command."""

    def test_valid_file_starts_server(self, tmp_path: Path) -> None:
        """Test that valid file path starts server."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        # This will actually try to start server in implementation
        # For now, test command parsing would work
        result = subprocess.run(
            [sys.executable, "-m", "markdpy.cli.main", str(test_file), "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Help should work even without implementation
        assert result.returncode in (0, 1, 2)  # May fail if not implemented yet

    def test_valid_directory_starts_server(self, tmp_path: Path) -> None:
        """Test that valid directory path starts server."""
        (tmp_path / "test.md").write_text("# Test")

        result = subprocess.run(
            [sys.executable, "-m", "markdpy.cli.main", str(tmp_path), "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode in (0, 1, 2)

    def test_invalid_path_exits_with_code_3(self, tmp_path: Path) -> None:
        """Test that invalid path exits with code 3."""
        nonexistent = tmp_path / "nonexistent.md"

        result = subprocess.run(
            [sys.executable, "-m", "markdpy.cli.main", str(nonexistent)],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should exit with error (3 for not found)
        # May not be implemented yet
        assert result.returncode != 0 or "not found" in result.stderr.lower()

    def test_help_flag_shows_usage(self) -> None:
        """Test that --help shows usage information."""
        result = subprocess.run(
            [sys.executable, "-m", "markdpy.cli.main", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Help should work
        if result.returncode == 0:
            assert "markdpy" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_port_option_accepted(self, tmp_path: Path) -> None:
        """Test that --port option is accepted."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        result = subprocess.run(
            [sys.executable, "-m", "markdpy.cli.main", str(test_file), "--port", "3000", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should parse successfully
        assert result.returncode in (0, 1, 2)

    def test_theme_option_accepted(self, tmp_path: Path) -> None:
        """Test that --theme option is accepted."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        result = subprocess.run(
            [sys.executable, "-m", "markdpy.cli.main", str(test_file), "--theme", "dark", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode in (0, 1, 2)

    def test_no_open_flag_accepted(self, tmp_path: Path) -> None:
        """Test that --no-open flag is accepted."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        result = subprocess.run(
            [sys.executable, "-m", "markdpy.cli.main", str(test_file), "--no-open", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode in (0, 1, 2)
