"""Seed starter content for a fresh LocalNotion install."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import ulid as ulid_lib

from localnotion.core.models import Page

logger = logging.getLogger(__name__)

# Titles referenced in wiki-links — must match exactly
_TITLES = [
    "Welcome to LocalNotion",
    "Project Dashboard",
    "Knowledge Base",
    "Meeting Notes",
    "Research Lab",
    "Product Roadmap",
    "Reading List",
    "Quick Reference",
]


def _make_page(
    title: str,
    tags: list[str],
    content: str,
    favorite: bool = False,
) -> Page:
    now = datetime.now(timezone.utc)
    return Page(
        id=str(ulid_lib.ULID()),
        title=title,
        content=content,
        type="page",
        status="active",
        tags=tags,
        workspace="default",
        icon="",
        cover="",
        is_favorite=favorite,
        created_at=now,
        modified_at=now,
    )


def create_seed_pages() -> list[Page]:
    """Return the starter pages for a fresh install."""
    pages: list[Page] = []

    # 1. Welcome
    pages.append(_make_page(_TITLES[0], ["getting-started", "guide"], """\
# Welcome to LocalNotion

Your **local-first knowledge operating system** is ready.

LocalNotion keeps everything on your machine — no cloud, no sync delays, no subscriptions.
Every page is a plain Markdown file in `~/localnotion/pages/`.

## Getting Started

1. **Create pages** from the sidebar or the page list
2. **Link pages** using `[[wiki-links]]` — try clicking [[Knowledge Base]]
3. **Explore the graph** to see how your ideas connect
4. **Use AI chat** to ask questions about your knowledge base
5. **Run engines** to generate courses, specs, articles, or docs

## Key Features

| Feature | Description |
|---------|------------|
| Wiki-links | Connect pages with `[[Page Name]]` syntax |
| Graph view | Visual map of all page connections |
| AI chat | Ask questions, get answers from your pages |
| Tables | Structured data with filters and views |
| Engines | AI-powered content generation pipelines |
| Search | Semantic search with `Cmd+K` |

## Templates

Check out these starter pages:
- [[Project Dashboard]] — Track your projects
- [[Meeting Notes]] — Capture meeting outcomes
- [[Research Lab]] — Organize research with formulas
- [[Reading List]] — Track your reading

> **Tip**: Star your most-used pages to pin them in the sidebar.
""", favorite=True))

    # 2. Project Dashboard
    pages.append(_make_page(_TITLES[1], ["template", "project"], """\
# Project Dashboard

A central hub for tracking active projects and their status.

## Active Projects

| Project | Status | Priority | Owner | Due |
|---------|--------|----------|-------|-----|
| LocalNotion v1.0 | In Progress | High | Team | Q1 2026 |
| API Integration | Planning | Medium | Dev | Q2 2026 |
| Documentation | In Progress | Low | Docs | Ongoing |

## Sprint Board

### To Do
- [ ] Set up CI/CD pipeline
- [ ] Write API documentation
- [ ] Design landing page

### In Progress
- [ ] Implement search indexing
- [ ] Build table templates

### Done
- [x] Core page CRUD
- [x] Wiki-link extraction
- [x] Knowledge graph visualization
- [x] AI chat integration

## Notes

Link related research in [[Knowledge Base]] and track meetings in [[Meeting Notes]].
See the [[Product Roadmap]] for long-term planning.
"""))

    # 3. Knowledge Base
    pages.append(_make_page(_TITLES[2], ["knowledge", "wiki"], """\
# Knowledge Base

How to build and organize your personal knowledge system with LocalNotion.

## The Zettelkasten Method

LocalNotion is built around the *Zettelkasten* (slip-box) method:

1. **Capture** — Write atomic notes about single ideas
2. **Connect** — Link related notes with `[[wiki-links]]`
3. **Discover** — Use the graph view to find unexpected connections
4. **Create** — Synthesize linked notes into new insights

## Wiki-Link Syntax

```markdown
Link to a page: [[Page Title]]
Link with custom text: [[Page Title|display text]]
```

## Workspaces

Organize pages into workspaces for different contexts:
- `default` — General notes
- `work` — Professional projects
- `research` — Academic and research notes
- `personal` — Personal knowledge

## Best Practices

1. **One idea per page** — Keep pages focused
2. **Link liberally** — Every page should link to at least 2 others
3. **Use tags** — For cross-cutting categories
4. **Review regularly** — Visit the graph to find orphan pages
5. **Let structure emerge** — Don't force hierarchies

> See [[Quick Reference]] for Markdown syntax and [[Research Lab]] for research templates.
""", favorite=True))

    # 4. Meeting Notes
    pages.append(_make_page(_TITLES[3], ["template", "notes"], """\
# Meeting Notes

A template for capturing meeting outcomes and action items.

---

## Weekly Standup — Feb 14, 2026

**Attendees**: Alice, Bob, Charlie
**Duration**: 30 min

### Updates
- **Alice**: Completed the search indexing module. Starting on vector embeddings.
- **Bob**: Fixed 3 bugs in the page editor. PR ready for review.
- **Charlie**: Drafted the API documentation. Needs review.

### Decisions
1. Use `nomic-embed-text` for embeddings (local, fast, good quality)
2. Deploy to Docker by end of week

### Action Items
- [ ] Alice: Integrate vector search with Qdrant
- [ ] Bob: Merge PR #42 after review
- [ ] Charlie: Share docs link in [[Project Dashboard]]
- [x] All: Review the [[Product Roadmap]]

---

## How to Use This Template

1. Copy the structure above for each meeting
2. Fill in attendees, duration, and date
3. Capture key updates, decisions, and action items
4. Link related pages and projects
5. Check off action items as they're completed
"""))

    # 5. Research Lab
    pages.append(_make_page(_TITLES[4], ["research", "science"], """\
# Research Lab

A workspace for organizing research notes, formulas, and experiments.

## Current Research Topics

### Information Retrieval
Semantic search using dense vector embeddings:

$$\\text{similarity}(q, d) = \\frac{q \\cdot d}{\\|q\\| \\|d\\|}$$

Where $q$ is the query vector and $d$ is the document vector.

### Knowledge Graphs
Modeling relationships between concepts:

```
Page A --[[links]]--> Page B
Page B --[[links]]--> Page C
Page A --[[links]]--> Page C  (transitive closure)
```

### Natural Language Processing
Using local LLMs for text generation:
- **Ollama** for inference
- **qwen2.5:14b** for general tasks
- **nomic-embed-text** for embeddings

## Methodology

1. **Hypothesis** — State what you expect to find
2. **Data** — Gather and organize sources
3. **Analysis** — Apply techniques and record results
4. **Conclusion** — Summarize findings and link to [[Knowledge Base]]

## References

Track your reading in [[Reading List]] and share findings in [[Project Dashboard]].

> *"The measure of intelligence is the ability to change."* — Albert Einstein
"""))

    # 6. Product Roadmap
    pages.append(_make_page(_TITLES[5], ["planning", "roadmap"], """\
# Product Roadmap

Long-term planning for LocalNotion development.

## Q1 2026 — Foundation

- [x] Core page CRUD with markdown
- [x] Wiki-link extraction and graph
- [x] AI chat with local LLM
- [x] Table engine with templates
- [ ] Semantic search with Qdrant
- [ ] Content generation engines

## Q2 2026 — Growth

- [ ] Real-time collaboration
- [ ] Plugin system for extensions
- [ ] Mobile companion app
- [ ] Import from Notion, Obsidian, Logseq
- [ ] Export to PDF, DOCX, LaTeX

## Q3 2026 — Scale

- [ ] Self-hosted cloud sync (optional)
- [ ] End-to-end encryption
- [ ] API for third-party integrations
- [ ] Marketplace for templates and plugins

## Principles

1. **Local-first** — Your data stays on your machine
2. **Open format** — Plain Markdown files, no lock-in
3. **AI-native** — LLM integration at every level
4. **Extensible** — Plugins and engines for custom workflows

See [[Project Dashboard]] for current sprint status.
"""))

    # 7. Reading List
    pages.append(_make_page(_TITLES[6], ["reading", "books"], """\
# Reading List

Track books, articles, and papers you want to read or have read.

## Currently Reading

| Title | Author | Progress | Rating |
|-------|--------|----------|--------|
| Designing Data-Intensive Apps | Martin Kleppmann | 75% | - |
| The Staff Engineer's Path | Tanya Reilly | 40% | - |

## Completed

| Title | Author | Rating | Notes |
|-------|--------|--------|-------|
| How to Take Smart Notes | Sonke Ahrens | 5/5 | Core inspiration for [[Knowledge Base]] |
| Thinking, Fast and Slow | Daniel Kahneman | 4/5 | System 1/2 framework |
| The Pragmatic Programmer | Hunt & Thomas | 5/5 | Every dev should read this |
| Atomic Habits | James Clear | 4/5 | Small changes, remarkable results |

## Want to Read

- [ ] "A Philosophy of Software Design" by John Ousterhout
- [ ] "Refactoring" by Martin Fowler
- [ ] "Building a Second Brain" by Tiago Forte
- [ ] "The Art of Doing Science and Engineering" by Richard Hamming

## Notes

Link book notes to relevant research in [[Research Lab]].
Use `[[Book Title]]` to create dedicated note pages for each book.
"""))

    # 8. Quick Reference
    pages.append(_make_page(_TITLES[7], ["reference", "cheatsheet"], """\
# Quick Reference

Essential LocalNotion shortcuts and Markdown syntax.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+K` | Open search |
| `Cmd+S` | Save current page |
| `Cmd+N` | New page |
| `Cmd+B` | Bold text |
| `Cmd+I` | Italic text |

## Markdown Syntax

### Text Formatting
```markdown
**bold** and *italic* and ~~strikethrough~~
`inline code` and [links](https://example.com)
```

### Headers
```markdown
# H1  ## H2  ### H3  #### H4
```

### Lists
```markdown
- Bullet point
  - Nested item
1. Numbered list
- [ ] Task checkbox
- [x] Completed task
```

### Wiki-Links
```markdown
[[Page Name]]
[[Page Name|Custom Display Text]]
```

### Code Blocks
Use triple backticks with language name:

```python
def hello():
    print("Hello, LocalNotion!")
```

### Math (KaTeX)
Inline: `$E = mc^2$` renders as $E = mc^2$

Block:
$$\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$

### Tables
```markdown
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
```

### Blockquotes
```markdown
> This is a blockquote
> It can span multiple lines
```

---

For more tips, see [[Knowledge Base]] and [[Welcome to LocalNotion]].
""", favorite=True))

    return pages


def seed_if_empty(store: "PageStore", index: "PageIndex") -> int:  # noqa: F821
    """Create starter pages if the store is empty. Returns count of pages created."""
    existing = store.list_all()
    if existing:
        return 0

    pages = create_seed_pages()
    for page in pages:
        page.word_count = page.compute_word_count()
        page.links = page.extract_wiki_links()
        store.save(page)
        index.upsert_page(page)

    logger.info("Seeded %d starter pages", len(pages))
    return len(pages)
