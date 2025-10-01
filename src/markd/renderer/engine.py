"""Markdown rendering engine."""

from functools import lru_cache
from typing import Any

import markdown
from markdown.extensions import Extension

from markd.config.models import RenderConfig


class MarkdownRenderer:
    """Renders Markdown to HTML with configured extensions."""

    def __init__(self, config: RenderConfig | None = None) -> None:
        """Initialize renderer with configuration."""
        self.config = config or RenderConfig.default()
        self._md = self._create_markdown_instance()

    def _create_markdown_instance(self) -> markdown.Markdown:
        """Create configured markdown instance."""
        return markdown.Markdown(
            extensions=self.config.extensions,
            extension_configs=self.config.extension_configs,
        )

    @lru_cache(maxsize=128)
    def render(self, content: str) -> str:
        """
        Render Markdown content to HTML.

        Args:
            content: Raw Markdown string

        Returns:
            Rendered HTML string
        """
        # Reset the markdown instance for fresh render
        self._md.reset()
        return self._md.convert(content)

    def render_file(self, content: str) -> tuple[str, str]:
        """
        Render file and extract TOC if enabled.

        Args:
            content: Raw Markdown string

        Returns:
            Tuple of (rendered_html, toc_html)
        """
        html = self.render(content)
        toc = ""

        # Extract TOC if available
        if self.config.enable_toc and hasattr(self._md, "toc"):
            toc = self._md.toc  # type: ignore

        return html, toc
