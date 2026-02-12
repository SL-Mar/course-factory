"""Text extraction utilities (HTML stripping, Notion block conversion)."""

from __future__ import annotations

from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    """Simple HTML-to-text converter using stdlib html.parser."""

    SKIP_TAGS = {"script", "style", "noscript", "svg", "head"}

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        if tag in ("br", "p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr"):
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._parts.append(data)

    def get_text(self) -> str:
        raw = "".join(self._parts)
        # Collapse runs of whitespace while preserving paragraph breaks
        lines = raw.split("\n")
        cleaned = [" ".join(line.split()) for line in lines]
        # Remove excessive blank lines
        result: list[str] = []
        blank_count = 0
        for line in cleaned:
            if not line:
                blank_count += 1
                if blank_count <= 2:
                    result.append("")
            else:
                blank_count = 0
                result.append(line)
        return "\n".join(result).strip()


def extract_html(html: str) -> str:
    """Extract readable text from HTML content."""
    extractor = _TextExtractor()
    extractor.feed(html)
    return extractor.get_text()
