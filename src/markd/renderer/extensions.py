"""Custom Markdown extensions for markd."""

import re
from markdown import Extension
from markdown.postprocessors import Postprocessor


class ExternalLinkProcessor(Postprocessor):
    """Add target='_blank' and rel='noopener noreferrer' to external links."""
    
    def run(self, text: str) -> str:
        """Process HTML to add attributes to external links."""
        # Match <a href="..."> tags that start with http:// or https://
        pattern = r'<a href="(https?://[^"]+)">'
        replacement = r'<a href="\1" target="_blank" rel="noopener noreferrer">'
        return re.sub(pattern, replacement, text)


class ExternalLinkExtension(Extension):
    """Extension to handle external links."""
    
    def extendMarkdown(self, md):  # type: ignore
        """Register the postprocessor."""
        md.postprocessors.register(
            ExternalLinkProcessor(md),
            'external_links',
            5  # Priority
        )


def makeExtension(**kwargs):  # type: ignore
    """Create extension instance."""
    return ExternalLinkExtension(**kwargs)
