"""Static site generator for exporting Markdown to HTML."""

import shutil
from pathlib import Path

from markdpy.renderer import MarkdownRenderer


class StaticSiteGenerator:
    """Generate static HTML files from Markdown sources."""

    def __init__(
        self,
        renderer: MarkdownRenderer | None = None,
        theme: str = "light",
        minify: bool = False,
    ) -> None:
        """
        Initialize static site generator.

        Args:
            renderer: Markdown renderer instance (creates new if None)
            theme: Theme name for styling
            minify: Whether to minify HTML output
        """
        self.renderer = renderer or MarkdownRenderer()
        self.theme = theme
        self.minify = minify

    def export_file(
        self, source: Path, output_dir: Path, relative_path: Path | None = None
    ) -> Path:
        """
        Export a single Markdown file to HTML.

        Args:
            source: Source Markdown file path
            output_dir: Output directory for generated HTML
            relative_path: Relative path for output (defaults to source name)

        Returns:
            Path to generated HTML file

        Raises:
            FileNotFoundError: If source file doesn't exist
            ValueError: If source is not a Markdown file
        """
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        if source.suffix.lower() not in (".md", ".markdown"):
            raise ValueError(f"Not a Markdown file: {source}")

        # Determine output path
        if relative_path:
            output_file = output_dir / relative_path.with_suffix(".html")
        else:
            output_file = output_dir / source.with_suffix(".html").name

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Read and render Markdown
        content = source.read_text(encoding="utf-8")
        rendered_html = self.renderer.render(content)

        # Create HTML document
        html = self._create_html_document(
            title=source.stem,
            content=rendered_html,
            theme=self.theme,
        )

        # Minify if requested
        if self.minify:
            html = self._minify_html(html)

        # Write output
        output_file.write_text(html, encoding="utf-8")

        return output_file

    def export_directory(
        self, source: Path, output_dir: Path, recursive: bool = True
    ) -> list[Path]:
        """
        Export all Markdown files in a directory to HTML.

        Args:
            source: Source directory containing Markdown files
            output_dir: Output directory for generated HTML
            recursive: Whether to process subdirectories

        Returns:
            List of generated HTML file paths

        Raises:
            NotADirectoryError: If source is not a directory
        """
        if not source.is_dir():
            raise NotADirectoryError(f"Not a directory: {source}")

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find all Markdown files
        pattern = "**/*.md" if recursive else "*.md"
        md_files = list(source.glob(pattern))

        # Export each file
        exported_files = []
        for md_file in sorted(md_files):
            relative_path = md_file.relative_to(source)
            output_file = self.export_file(md_file, output_dir, relative_path)
            exported_files.append(output_file)

        # Copy static assets if they exist (now in root directory)
        static_dir = Path(__file__).parent.parent.parent.parent / "static"
        if static_dir.exists():
            output_static = output_dir / "static"
            if output_static.exists():
                shutil.rmtree(output_static)
            shutil.copytree(static_dir, output_static)

        return exported_files

    def _create_html_document(self, title: str, content: str, theme: str = "light") -> str:
        """
        Create a standalone HTML document.

        Args:
            title: Document title
            content: Rendered Markdown content
            theme: Theme name

        Returns:
            Complete HTML document string
        """
        # Minimal HTML template for exported files
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <link rel="stylesheet" href="static/css/style.css">
    <link rel="stylesheet" href="static/css/themes/{theme}.css">
</head>
<body>
    <div class="container">
        <article class="rendered-content">
{content}
        </article>
    </div>
</body>
</html>"""
        return html

    def _minify_html(self, html: str) -> str:
        """
        Minify HTML by removing unnecessary whitespace.

        Args:
            html: HTML string to minify

        Returns:
            Minified HTML string
        """
        # Simple minification: remove extra whitespace between tags
        import re

        # Remove comments
        html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

        # Remove whitespace between tags
        html = re.sub(r">\s+<", "><", html)

        # Remove leading/trailing whitespace per line
        html = "\n".join(line.strip() for line in html.splitlines() if line.strip())

        return html
