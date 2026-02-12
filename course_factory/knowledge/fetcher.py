"""Source fetchers for Notion pages, GitHub repos, and web URLs."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from urllib.request import Request, urlopen
from urllib.error import URLError

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """Result of fetching a single source."""

    source_type: str
    slug: str
    content: str
    metadata: dict = field(default_factory=dict)
    error: str = ""


# ---------------------------------------------------------------------------
# Notion
# ---------------------------------------------------------------------------

def fetch_notion_page(page_id: str, api_key: str) -> FetchResult:
    """Fetch all blocks from a Notion page and extract text content."""
    clean_id = page_id.replace("-", "")
    slug = f"notion-{clean_id[:12]}"

    if not api_key:
        return FetchResult(
            source_type="notion", slug=slug, content="",
            error="No Notion API key configured",
        )

    try:
        # Fetch page title
        page_url = f"https://api.notion.com/v1/pages/{page_id}"
        req = Request(page_url, headers={
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2022-06-28",
        })
        with urlopen(req, timeout=30) as resp:
            page_data = json.loads(resp.read())

        title = _extract_notion_title(page_data)

        # Fetch blocks
        blocks_url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
        all_blocks: list[dict] = []
        while blocks_url:
            req = Request(blocks_url, headers={
                "Authorization": f"Bearer {api_key}",
                "Notion-Version": "2022-06-28",
            })
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            all_blocks.extend(data.get("results", []))
            if data.get("has_more"):
                cursor = data["next_cursor"]
                blocks_url = (
                    f"https://api.notion.com/v1/blocks/{page_id}/children"
                    f"?page_size=100&start_cursor={cursor}"
                )
            else:
                blocks_url = ""

        content = _blocks_to_markdown(all_blocks, title)
        return FetchResult(
            source_type="notion", slug=slug, content=content,
            metadata={"page_id": page_id, "title": title},
        )

    except (URLError, OSError, json.JSONDecodeError) as exc:
        logger.error("Notion fetch failed for %s: %s", page_id, exc)
        return FetchResult(
            source_type="notion", slug=slug, content="",
            error=str(exc),
        )


def _extract_notion_title(page_data: dict) -> str:
    """Extract page title from Notion page properties."""
    props = page_data.get("properties", {})
    for prop in props.values():
        if prop.get("type") == "title":
            title_parts = prop.get("title", [])
            return "".join(t.get("plain_text", "") for t in title_parts)
    return "Untitled"


def _blocks_to_markdown(blocks: list[dict], title: str = "") -> str:
    """Convert Notion block objects to markdown text."""
    lines: list[str] = []
    if title:
        lines.append(f"# {title}\n")

    for block in blocks:
        btype = block.get("type", "")
        data = block.get(btype, {})

        if btype == "paragraph":
            text = _rich_text(data)
            lines.append(text + "\n")
        elif btype.startswith("heading_"):
            level = int(btype[-1])
            text = _rich_text(data)
            lines.append(f"{'#' * level} {text}\n")
        elif btype == "bulleted_list_item":
            text = _rich_text(data)
            lines.append(f"- {text}")
        elif btype == "numbered_list_item":
            text = _rich_text(data)
            lines.append(f"1. {text}")
        elif btype == "code":
            text = _rich_text(data)
            lang = data.get("language", "")
            lines.append(f"```{lang}\n{text}\n```\n")
        elif btype == "quote":
            text = _rich_text(data)
            lines.append(f"> {text}\n")
        elif btype == "callout":
            text = _rich_text(data)
            lines.append(f"> {text}\n")
        elif btype == "divider":
            lines.append("---\n")
        elif btype == "to_do":
            text = _rich_text(data)
            checked = data.get("checked", False)
            lines.append(f"- [{'x' if checked else ' '}] {text}")
        elif btype == "toggle":
            text = _rich_text(data)
            lines.append(f"<details><summary>{text}</summary></details>\n")

    return "\n".join(lines)


def _rich_text(data: dict) -> str:
    """Extract plain text from a rich_text array."""
    parts = data.get("rich_text", [])
    return "".join(p.get("plain_text", "") for p in parts)


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

def fetch_github_repo(owner: str, repo: str, token: str = "") -> FetchResult:
    """Fetch README + key .md/.py files from a GitHub repo."""
    slug = f"github-{owner}-{repo}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    content_parts: list[str] = [f"# GitHub: {owner}/{repo}\n"]

    try:
        # Fetch README
        readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        req = Request(readme_url, headers=headers)
        try:
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            import base64
            readme_content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
            content_parts.append("## README\n")
            content_parts.append(readme_content + "\n")
        except URLError:
            content_parts.append("(No README found)\n")

        # Fetch repo tree for docs/src .md and .py files
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
        req = Request(tree_url, headers=headers)
        try:
            with urlopen(req, timeout=30) as resp:
                tree_data = json.loads(resp.read())

            # Collect interesting files (max 20)
            interesting: list[str] = []
            for item in tree_data.get("tree", []):
                path = item.get("path", "")
                if item.get("type") != "blob":
                    continue
                if len(interesting) >= 20:
                    break
                if path.endswith((".md", ".py")) and (
                    path.startswith(("docs/", "src/", "doc/"))
                    or path.count("/") == 0
                ):
                    if path.lower() not in ("readme.md",):
                        interesting.append(path)

            for fpath in interesting[:10]:
                file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{fpath}"
                req = Request(file_url, headers=headers)
                try:
                    with urlopen(req, timeout=15) as resp:
                        fdata = json.loads(resp.read())
                    import base64
                    file_content = base64.b64decode(fdata.get("content", "")).decode(
                        "utf-8", errors="replace"
                    )
                    content_parts.append(f"\n## {fpath}\n")
                    content_parts.append(file_content[:3000] + "\n")
                except (URLError, OSError):
                    pass

        except (URLError, OSError):
            pass

        content = "\n".join(content_parts)
        return FetchResult(
            source_type="github", slug=slug, content=content,
            metadata={"owner": owner, "repo": repo},
        )

    except (URLError, OSError, json.JSONDecodeError) as exc:
        logger.error("GitHub fetch failed for %s/%s: %s", owner, repo, exc)
        return FetchResult(
            source_type="github", slug=slug, content="",
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# Web URL
# ---------------------------------------------------------------------------

def fetch_url(url: str) -> FetchResult:
    """Fetch a web URL and extract text content."""
    # Create a filesystem-safe slug from the URL
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", url.split("//", 1)[-1])[:60]
    slug = f"web-{slug}".rstrip("-")

    try:
        req = Request(url, headers={
            "User-Agent": "CourseFactory/0.1 (educational content extraction)",
        })
        with urlopen(req, timeout=30) as resp:
            raw = resp.read()
            charset = resp.headers.get_content_charset() or "utf-8"
            html = raw.decode(charset, errors="replace")

        from course_factory.knowledge.extractor import extract_html
        text = extract_html(html)

        return FetchResult(
            source_type="url", slug=slug, content=text,
            metadata={"url": url},
        )

    except (URLError, OSError) as exc:
        logger.error("URL fetch failed for %s: %s", url, exc)
        return FetchResult(
            source_type="url", slug=slug, content="",
            error=str(exc),
        )
