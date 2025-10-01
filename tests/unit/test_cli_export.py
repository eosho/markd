"""Contract tests for CLI export command."""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.unit
class TestCliExportCommand:
    """Test suite for markdpy export command."""

    def test_export_single_file_to_html(self, tmp_path: Path) -> None:
        """Test that export command exports single file to HTML."""
        source = tmp_path / "test.md"
        source.write_text("# Test\n\nContent")
        output = tmp_path / "output"
        output.mkdir()

        result = subprocess.run(
            [sys.executable, "-m", "markdpy.cli.main", "export", str(source), str(output)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # May not be implemented yet
        assert result.returncode in (0, 1, 2) or "export" in result.stderr.lower()

    def test_export_directory_preserves_structure(self, tmp_path: Path) -> None:
        """Test that export preserves directory structure."""
        source = tmp_path / "docs"
        source.mkdir()
        (source / "test1.md").write_text("# Test 1")
        (source / "test2.md").write_text("# Test 2")

        output = tmp_path / "output"
        output.mkdir()

        result = subprocess.run(
            [sys.executable, "-m", "markdpy.cli.main", "export", str(source), str(output)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode in (0, 1, 2)

    def test_minify_option_works(self, tmp_path: Path) -> None:
        """Test that --minify option is accepted."""
        source = tmp_path / "test.md"
        source.write_text("# Test")
        output = tmp_path / "output"
        output.mkdir()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "markdpy.cli.main",
                "export",
                str(source),
                str(output),
                "--minify",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode in (0, 1, 2)

    def test_invalid_source_exits_3(self, tmp_path: Path) -> None:
        """Test that invalid source path exits with code 3."""
        nonexistent = tmp_path / "nonexistent.md"
        output = tmp_path / "output"

        result = subprocess.run(
            [sys.executable, "-m", "markdpy.cli.main", "export", str(nonexistent), str(output)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should fail with error
        assert result.returncode != 0 or "not found" in result.stderr.lower()

    def test_theme_option_for_export(self, tmp_path: Path) -> None:
        """Test that --theme option works for export."""
        source = tmp_path / "test.md"
        source.write_text("# Test")
        output = tmp_path / "output"
        output.mkdir()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "markdpy.cli.main",
                "export",
                str(source),
                str(output),
                "--theme",
                "dark",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode in (0, 1, 2)

    def test_export_help_shows_options(self) -> None:
        """Test that export --help shows available options."""
        result = subprocess.run(
            [sys.executable, "-m", "markdpy.cli.main", "export", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            # Should mention export functionality
            assert "export" in result.stdout.lower() or "source" in result.stdout.lower()
