"""Custom Markdown extension to process internal links."""

from pathlib import Path
from urllib.parse import quote, urlparse
from xml.etree import ElementTree

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor


class LinkProcessor(Treeprocessor):
    """Process links to handle .md files and external links."""

    def __init__(self, md, base_path: Path | None = None):
        """Initialize link processor.

        Args:
            md: Markdown instance
            base_path: Base path for resolving relative links
        """
        super().__init__(md)
        self.base_path = base_path or Path.cwd()

    def run(self, root: ElementTree.Element) -> ElementTree.Element:
        """Process all links in the document.

        Args:
            root: Root element of the parsed document

        Returns:
            Modified root element
        """
        self._process_element(root)
        return root

    def _process_element(self, element: ElementTree.Element) -> None:
        """Recursively process an element and its children.

        Args:
            element: Element to process
        """
        # Process anchor tags (but not if they contain images - those are badge links)
        if element.tag == "a":
            href = element.get("href", "")
            # Check if this anchor contains an image (badge/shield links)
            has_image = any(child.tag == "img" for child in element)

            if href and not has_image:
                element.set("href", self._transform_link(href))

                # Add target="_blank" for external links
                if self._is_external_link(href):
                    element.set("target", "_blank")
                    element.set("rel", "noopener noreferrer")
            elif href and has_image:
                # For badge/image links, add target="_blank" if external
                if self._is_external_link(href):
                    element.set("target", "_blank")
                    element.set("rel", "noopener noreferrer")

        # Process children recursively
        for child in element:
            self._process_element(child)

    def _transform_link(self, href: str) -> str:
        """Transform a link href.

        Args:
            href: Original href value

        Returns:
            Transformed href
        """
        # Skip anchors, external links, and absolute paths
        if href.startswith(("#", "http://", "https://", "ftp://", "mailto:", "/")):
            return href

        # Handle relative file links (including .md, .markdown, and files without extension)
        # Check if it looks like a relative file path (contains . or no / or single word)
        is_relative_file = (
            "." in href  # Has extension or relative path
            or "/" not in href  # Single file name
            or href.endswith((".md", ".markdown", ".txt"))  # Known text formats
        )

        if is_relative_file:
            # Handle query strings and anchors
            parts = href.split("#", 1)
            path_part = parts[0]
            anchor = f"#{parts[1]}" if len(parts) > 1 else ""

            # URL encode the path (keep extension intact)
            encoded_path = quote(path_part)

            # Convert to /view/ endpoint
            return f"/view/{encoded_path}{anchor}"

        return href

    def _is_external_link(self, href: str) -> bool:
        """Check if a link is external.

        Args:
            href: Link href to check

        Returns:
            True if external, False otherwise
        """
        if href.startswith(("#", "/")):
            return False

        parsed = urlparse(href)
        return bool(parsed.scheme and parsed.netloc)


class LinkProcessorExtension(Extension):
    """Markdown extension to process links."""

    def __init__(self, **kwargs):
        """Initialize extension."""
        self.config = {
            "base_path": [Path.cwd(), "Base path for resolving relative links"],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):  # noqa: N802
        """Register the extension.

        Args:
            md: Markdown instance
        """
        base_path = self.getConfig("base_path")
        processor = LinkProcessor(md, base_path)
        md.treeprocessors.register(processor, "link_processor", 10)


def makeExtension(**kwargs):  # noqa: N802
    """Create the extension."""
    return LinkProcessorExtension(**kwargs)
