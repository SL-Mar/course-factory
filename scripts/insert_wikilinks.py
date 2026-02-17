#!/usr/bin/env python3
"""Insert [[wiki-links]] across all Katja pages to build a knowledge graph.

Usage:
    python scripts/insert_wikilinks.py               # dry-run (default)
    python scripts/insert_wikilinks.py --execute      # apply changes

Can run inside Docker:
    docker compose exec app python /app/scripts/insert_wikilinks.py --execute
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path


# ── Configuration ──

# Pages with these title prefixes are noise — skip as link targets
SKIP_TITLE_PREFIXES = [
    "No New Articles",
    "No Recent",
    "As No Articles",
    "As There Were No",
    "There Are No",
    "No New Information",
]

# Pages with these exact titles are too generic to link to
SKIP_TITLES = {
    "Test", "Basic", "Introduction", "Untitled", "UnTtitled",
    "Task", "Task 1", "Task 2", "Task 3",
    "Besedilo", "Frizer", "Razprava", "Slovene", "Telo", "Italian",
    "Market View", "Welcome to Katja", "Project Dashboard",
    "Knowledge Base", "Meeting Notes", "Research Lab",
    "Product Roadmap", "Reading List", "Quick Reference",
}

# Workspaces where pages are mostly auto-generated — only link key pages
AUTO_WORKSPACES = {"trading", "admin"}

# Pages in auto workspaces that ARE worth linking to
FORCE_LINKABLE_TRADING = {
    "Trading Ideas",
    "Saturday Trading Call",
    "Training Datasets",
    "Fine Tuned Models In Finance",
    "Designing A Code Fine Tuning Llm From Timescaledb Fundamentals Data",
    "Characteristic Managed Momentum  Validation Study Against Buy And Hold During",
}


# ── Explicit concept → page title mappings for cross-workspace linking ──

CONCEPT_LINKS: dict[str, list[str]] = {
    # WindMar project + specs
    r"\bwindmar\b": ["Windmar Project"],
    r"\bspec\s*p0\b": ["Spec P0 — Webgl Weather Visualization"],
    r"\bspec\s*p1\b": ["Spec P1 — Extended Weather Fields & Current Adjusted Routing"],
    r"\bspec\s*p2\b(?!\s*[a-d])": ["Spec P2 — Ais Validation Pipeline & Historical Performance Benchmarking"],
    r"\bspec\s*p2\s*a\b": ["Spec P2A — Era5 Corridor Archive & Eof Decomposition"],
    r"\bspec\s*p2\s*b\b": ["Spec P2B — Wasserstein Clustering & Analogue Sequence Library"],
    r"\bspec\s*p2\s*c\b": ["Spec P2C — Operational Loop  Gfs→Analogue Splicing & Daily Re Attachment"],
    r"\bspec\s*p2\s*d\b": ["Spec P2D — Retrospective Validation & Ensemble Quality Calibration"],
    r"\bspec\s*p3\b": ["Spec P3 — Route Strip Chart & Voyage Interpretability Report"],
    r"\bera5\b": ["Spec P2A — Era5 Corridor Archive & Eof Decomposition"],
    r"\bwasserstein\b": ["Spec P2B — Wasserstein Clustering & Analogue Sequence Library"],
    r"\broute\s*strip\b": ["Spec P3 — Route Strip Chart & Voyage Interpretability Report"],
    r"\bais\s+validation\b": ["Spec P2 — Ais Validation Pipeline & Historical Performance Benchmarking"],
    r"\bseakeeping\b": ["Parametric Roll Detection  Enhancing Windmar With Academic Research"],
    r"\bmaritime\s+os\b": ["Maritime Os Full System Specification"],
    r"\bshipboard\s+os\b": ["Shipboard Os Onboard Intelligence Platform"],
    r"\bgisis\b": ["Gisis Port Facilities Database  Access & Integration Guide"],
    r"\bellipse.n\b": ["Physics Informed Neural Networks For Ship Seakeeping From Ellipse N Data (Conceptual"],

    # QuantMar
    r"\bquantmar\b": ["Quantmar Unified Specification"],
    r"\bmean\s+reversion\b": ["Strategy 4 — Optimal Mean Reversion"],
    r"\bstatistical\s+arbitrage\b": ["Strategy 5 — Conditional Factor Statistical Arbitrage"],
    r"\bfactor\s+arbitrage\b": ["Strategy 5 — Conditional Factor Statistical Arbitrage"],
    r"\bskewness\s+parity\b": ["Strategy 7 — Skewness Parity Portfolio"],
    r"\brisk\s+parity\b(?!.*principles)": ["Strategy 9 — Robust Risk Parity With Fundamentals"],

    # Q2C chapters/modules
    r"\bmodule\s*0\b": ["Module 0  Crash Courses"],
    r"\bmodule\s*1\b": ["Module 1  Quant Finance Basics"],
    r"\bmodule\s*2\b": ["Module 2  Data Layer (Eodhd)"],

    # Development / products
    r"\bcourse\s+factory\b": ["Katja — Technical Specification"],
    r"\bkatja\b": ["Katja — Technical Specification"],
    r"\bagentic\s+ai\b": ["Agentic Ai"],
    r"\bmarine\s+osint\b": ["Marine Osint Full Specification"],

    # Articles / research
    r"\b(?:dcr|distance.to.criticality)\b": ["Distance To Criticality Risk Dcr Research Paper"],
    r"\bcontinual\s+learning\b": ["Shared Lora Subspaces For Continual Learning"],
    r"\balpha\s+discovery\b": ["Autonomous Alpha Discovery Through Code Based Agentic Research  A Self Improving"],

    # MarChat / maritime
    r"\bmarchat\b": ["Maritime Legal Assistant   Project Specification"],
    r"\bsolas\b": ["Maritime Legal Assistant   Project Specification"],
    r"\bstcw\b": ["Maritime Legal Assistant   Project Specification"],

    # Zvezda
    r"\bdrydock\b": ["Drydock 2024"],
    r"\bzvezda\b(?!.*project)": ["Zvezda"],

    # Backtesting/risk mgmt references
    r"\bbacktest(?:ing)?\b": ["Chapter 9  Backtesting Philosophy And Common Pitfalls"],
    r"\brisk\s+management\b": ["Chapter 10  Risk Management Principles"],
    r"\beodhd\b": ["Chapter 12  Eodhd Api Integration"],
    r"\btimescaledb\b": ["Chapter 13  Database Setup   Postgresql And Timescaledb"],
    r"\bn8n\b": ["Chapter 3  N8N For Trading Automation"],
}


# ── Workspace-level "See also" connections ──

WORKSPACE_RELATED: dict[str, list[str]] = {
    "windmar": [
        "Windmar Project",
        "Spec P0 — Webgl Weather Visualization",
        "Spec P1 — Extended Weather Fields & Current Adjusted Routing",
        "Spec P2 — Ais Validation Pipeline & Historical Performance Benchmarking",
        "Spec P2A — Era5 Corridor Archive & Eof Decomposition",
        "Spec P2B — Wasserstein Clustering & Analogue Sequence Library",
        "Spec P2C — Operational Loop  Gfs→Analogue Splicing & Daily Re Attachment",
        "Spec P2D — Retrospective Validation & Ensemble Quality Calibration",
        "Spec P3 — Route Strip Chart & Voyage Interpretability Report",
        "Maritime Os Full System Specification",
        "Data Sources Free Apis Rag",
        "Data Sources Free Osint",
    ],
    "quantmar": [
        "Quantmar Unified Specification",
        "Quant Neo  Virtual Ml Engineer For Timescaledb Financial Intelligence",
        "Strategy 4 — Optimal Mean Reversion",
        "Strategy 5 — Conditional Factor Statistical Arbitrage",
        "Strategy 7 — Skewness Parity Portfolio",
        "Strategy 9 — Robust Risk Parity With Fundamentals",
        "Chapter 9  Backtesting Philosophy And Common Pitfalls",
    ],
    "q2c": [
        "Module 0  Crash Courses",
        "Module 1  Quant Finance Basics",
        "Module 2  Data Layer (Eodhd)",
    ],
    "articles": [
        "Article Publication Roadmap   January 2026",
        "Distance To Criticality Risk Dcr Research Paper",
        "Dcr Editorial Strategy",
        "Ml Research",
        "Shared Lora Subspaces For Continual Learning",
    ],
    "development": [
        "Katja — Technical Specification",
        "Katja — Commercial Specification",
        "Agentic Ai",
        "Cli First Project Template",
        "Building Your Own Virtual Software Engineer",
    ],
    "marchat": [
        "Maritime Legal Assistant   Project Specification",
    ],
    "marine-issues": [
        "Marine Osint Full Specification",
        "Miros Group   Ui Ux Benchmark Analysis",
    ],
    "zvezda": [
        "Zvezda",
        "Drydock 2024",
    ],
}


# Q2C chapter sequence for next/prev links
Q2C_CHAPTER_ORDER = [
    "Chapter 1  Python For Quantitative Trading",
    "Chapter 2  Typescript For Trading Interfaces",
    "Chapter 3  N8N For Trading Automation",
    "Chapter 4  Module 0 Capstone   Building The Foundation",
    "Chapter 5  Introduction To Quantitative Trading",
    "Chapter 6  Return, Risk, And Portfolio Metrics",
    "Chapter 7  Market Microstructure",
    "Chapter 8  Factor Investing Framework",
    "Chapter 9  Backtesting Philosophy And Common Pitfalls",
    "Chapter 10  Risk Management Principles",
    "Chapter 11  Data Architecture Overview",
    "Chapter 12  Eodhd Api Integration",
    "Chapter 13  Database Setup   Postgresql And Timescaledb",
    "Chapter 14  Data Validation And Quality Control",
    "Chapter 15  Building The Data Update Pipeline",
    "Chapter 16  Scheduling And Automation With N8N",
    "Chapter 17  Module 2 Capstone   Production Data System",
]


def load_pages(pages_dir: Path) -> list[dict]:
    """Load all pages with title, workspace, body, and path."""
    pages = []
    for md_file in sorted(pages_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^title:\s*(.+?)\s*$", text, re.MULTILINE)
        title = m.group(1).strip().strip("'\"") if m else ""
        wm = re.search(r"^workspace:\s*(\S+)", text, re.MULTILINE)
        ws = wm.group(1) if wm else "default"

        # Split frontmatter from body
        parts = text.split("---", 2)
        body = parts[2] if len(parts) >= 3 else text

        existing_links = set(re.findall(r"\[\[([^\]]+)\]\]", body))

        pages.append({
            "id": md_file.stem,
            "title": title,
            "workspace": ws,
            "body": body,
            "full_text": text,
            "path": md_file,
            "existing_links": existing_links,
        })
    return pages


def is_linkable(page: dict) -> bool:
    """Determine if a page should be a link target."""
    title = page["title"]
    if not title or len(title) < 5:
        return False
    if title in SKIP_TITLES:
        return False
    for prefix in SKIP_TITLE_PREFIXES:
        if title.startswith(prefix):
            return False
    # Auto workspaces: only allow force-listed pages
    if page["workspace"] in AUTO_WORKSPACES:
        return title in FORCE_LINKABLE_TRADING
    return True


def is_content_page(page: dict) -> bool:
    """Determine if a page has enough content to add links to."""
    title = page["title"]
    if not title:
        return False
    if title in SKIP_TITLES:
        return False
    for prefix in SKIP_TITLE_PREFIXES:
        if title.startswith(prefix):
            return False
    # Admin euros pages — skip
    if re.match(r"^\d+ Euros", title):
        return False
    # Daily trading summaries — skip (too many, auto-generated)
    if page["workspace"] == "trading":
        # Only process key trading pages
        if title not in FORCE_LINKABLE_TRADING and not title.startswith("Potential Breakout"):
            if re.match(r"^(Date |As Of |On |2025|2026|\d{4}\s)", title):
                return False
            if "Pre Market" in title or "Pre.Market" in title:
                return False
    # Body too short
    if len(page["body"].strip()) < 100:
        return False
    return True


def build_title_patterns(linkable_pages: list[dict]) -> list[tuple[re.Pattern, str]]:
    """Build regex patterns to match page titles in body text."""
    patterns = []
    for page in linkable_pages:
        title = page["title"]
        # Skip very long auto-generated titles
        if len(title) > 80:
            continue
        # Create case-insensitive pattern from title
        # Escape regex special chars, allow flexible whitespace
        escaped = re.escape(title)
        # Allow multi-space/dash variations
        flexible = re.sub(r"\\s+|\\ ", r"[\\s\\-]+", escaped)
        # Word boundary at start for short titles
        if len(title) < 20:
            pattern_str = r"\b" + flexible + r"\b"
        else:
            pattern_str = flexible
        try:
            pat = re.compile(pattern_str, re.IGNORECASE)
            patterns.append((pat, title))
        except re.error:
            continue
    return patterns


def build_concept_patterns() -> list[tuple[re.Pattern, list[str]]]:
    """Build concept → target title patterns."""
    patterns = []
    for pattern_str, targets in CONCEPT_LINKS.items():
        try:
            pat = re.compile(pattern_str, re.IGNORECASE)
            patterns.append((pat, targets))
        except re.error:
            continue
    return patterns


def is_inside_wikilink(text: str, pos: int) -> bool:
    """Check if position is inside an existing [[...]]."""
    # Search backwards for [[ without ]]
    before = text[:pos]
    last_open = before.rfind("[[")
    last_close = before.rfind("]]")
    if last_open > last_close:
        return True
    return False


def is_inside_codeblock(text: str, pos: int) -> bool:
    """Check if position is inside a fenced code block."""
    before = text[:pos]
    fences = re.findall(r"^```", before, re.MULTILINE)
    return len(fences) % 2 == 1


def is_inside_url(text: str, pos: int) -> bool:
    """Check if position is inside a URL or markdown link."""
    # Check for http(s):// context
    line_start = text.rfind("\n", 0, pos) + 1
    line = text[line_start:text.find("\n", pos)]
    # Check if we're inside (url) or [text](url)
    if re.search(r"\(https?://[^\)]*$", text[line_start:pos]):
        return True
    if re.search(r"https?://\S*$", text[line_start:pos]):
        return True
    return False


def is_inside_heading(text: str, pos: int) -> bool:
    """Check if position is on a heading line (# ...)."""
    line_start = text.rfind("\n", 0, pos) + 1
    line = text[line_start:text.find("\n", pos) if text.find("\n", pos) != -1 else len(text)]
    return line.lstrip().startswith("#")


def insert_inline_link(body: str, match_pos: int, match_len: int, target_title: str) -> str | None:
    """Insert a [[wiki-link]] at a match position, with safety checks."""
    if is_inside_wikilink(body, match_pos):
        return None
    if is_inside_codeblock(body, match_pos):
        return None
    if is_inside_url(body, match_pos):
        return None
    if is_inside_heading(body, match_pos):
        return None

    # Replace the matched text with [[target_title]]
    before = body[:match_pos]
    after = body[match_pos + match_len:]
    return before + f"[[{target_title}]]" + after


def get_see_also(page: dict, title_set: set[str], all_pages_by_title: dict) -> list[str]:
    """Get 'See also' links for a page based on workspace relationships."""
    see_also = []
    ws = page["workspace"]
    title = page["title"]

    # Workspace-level related pages
    if ws in WORKSPACE_RELATED:
        for related_title in WORKSPACE_RELATED[ws]:
            if related_title != title and related_title in title_set:
                see_also.append(related_title)

    # Q2C chapter sequence — add prev/next
    if ws == "q2c" and title in Q2C_CHAPTER_ORDER:
        idx = Q2C_CHAPTER_ORDER.index(title)
        if idx > 0:
            prev_title = Q2C_CHAPTER_ORDER[idx - 1]
            if prev_title in title_set and prev_title not in see_also:
                see_also.insert(0, prev_title)
        if idx < len(Q2C_CHAPTER_ORDER) - 1:
            next_title = Q2C_CHAPTER_ORDER[idx + 1]
            if next_title in title_set and next_title not in see_also:
                see_also.append(next_title)

        # Add parent module
        if idx <= 3:
            mod = "Module 0  Crash Courses"
        elif idx <= 9:
            mod = "Module 1  Quant Finance Basics"
        else:
            mod = "Module 2  Data Layer (Eodhd)"
        if mod != title and mod in title_set and mod not in see_also:
            see_also.insert(0, mod)

    # Q2C modules — add child chapters
    if title == "Module 0  Crash Courses":
        for ch in Q2C_CHAPTER_ORDER[:4]:
            if ch in title_set and ch not in see_also:
                see_also.append(ch)
    elif title == "Module 1  Quant Finance Basics":
        for ch in Q2C_CHAPTER_ORDER[4:10]:
            if ch in title_set and ch not in see_also:
                see_also.append(ch)
    elif title == "Module 2  Data Layer (Eodhd)":
        for ch in Q2C_CHAPTER_ORDER[10:]:
            if ch in title_set and ch not in see_also:
                see_also.append(ch)

    # Cross-workspace links for key pages
    cross_links = {
        "Windmar Project": [
            "Maritime Os Full System Specification",
            "Shipboard Os Onboard Intelligence Platform",
            "Data Sources Free Apis Rag",
        ],
        "Quantmar Unified Specification": [
            "Strategy 4 — Optimal Mean Reversion",
            "Strategy 5 — Conditional Factor Statistical Arbitrage",
            "Strategy 7 — Skewness Parity Portfolio",
            "Strategy 9 — Robust Risk Parity With Fundamentals",
            "Katja — Technical Specification",
        ],
        "Distance To Criticality Risk Dcr Research Paper": [
            "Dcr Editorial Strategy",
            "Dual Agent Architecture For Dcr System",
            "Article Publication Roadmap   January 2026",
            "Ml Research",
        ],
        "Dcr Editorial Strategy": [
            "Distance To Criticality Risk Dcr Research Paper",
            "Dual Agent Architecture For Dcr System",
            "Article Publication Roadmap   January 2026",
        ],
        "Article Publication Roadmap   January 2026": [
            "Distance To Criticality Risk Dcr Research Paper",
            "Dcr Editorial Strategy",
            "Ml Research",
            "Seven Years To One Year'S Salary  Lessons From A Part Time Trader'S Journey",
            "Shared Lora Subspaces For Continual Learning",
            "Autonomous Alpha Discovery Through Code Based Agentic Research  A Self Improving",
        ],
        "Ml Research": [
            "Shared Lora Subspaces For Continual Learning",
            "Autonomous Alpha Discovery Through Code Based Agentic Research  A Self Improving",
            "Distance To Criticality Risk Dcr Research Paper",
        ],
        "Katja — Technical Specification": [
            "Katja — Commercial Specification",
            "Cli First Project Template",
        ],
        "Katja — Commercial Specification": [
            "Katja — Technical Specification",
        ],
        "Maritime Legal Assistant   Project Specification": [
            "Marine Osint Full Specification",
        ],
        "Marine Osint Full Specification": [
            "Maritime Legal Assistant   Project Specification",
            "Miros Group   Ui Ux Benchmark Analysis",
        ],
        "Zvezda": [
            "Drydock 2024",
        ],
        "Drydock 2024": [
            "Zvezda",
            "2 Layers Of Primer Rudder And Keel",
            "Antifouling 2 Layers",
            "Hull Brushing",
            "Hull Polishing",
            "Keel Brushing And Resine Coating",
            "Epoxy Filling Of Rudder",
            "Brushing And Primer Of Propeller",
        ],
        "Building Your Own Virtual Software Engineer": [
            "Agentic Ai",
            "17 Agentic Ai Architectures  A Comprehensive Synthesis (Fareed Khan)",
            "Cli First Project Template",
        ],
        "Agentic Ai": [
            "17 Agentic Ai Architectures  A Comprehensive Synthesis (Fareed Khan)",
            "Building Your Own Virtual Software Engineer",
            "Building An Ai Native Engineering Team To Complete Long Tasks",
        ],
        "Miros Group   Ui Ux Benchmark Analysis": [
            "Windmar Project",
            "Marine Osint Full Specification",
        ],
        "Seven Years To One Year'S Salary  Lessons From A Part Time Trader'S Journey": [
            "Article Publication Roadmap   January 2026",
            "Trading Ideas",
        ],
        "Quant Neo  Virtual Ml Engineer For Timescaledb Financial Intelligence": [
            "Quantmar Unified Specification",
            "Quant Neo Implementation Assessment — Claude Code Instructions",
        ],
        "Quant Neo Implementation Assessment — Claude Code Instructions": [
            "Quant Neo  Virtual Ml Engineer For Timescaledb Financial Intelligence",
            "Quantmar Unified Specification",
        ],
        # Strategy pages → chapters + each other
        "Strategy 4 — Optimal Mean Reversion": [
            "Chapter 9  Backtesting Philosophy And Common Pitfalls",
            "Chapter 10  Risk Management Principles",
            "Quantmar Unified Specification",
            "Strategy 5 — Conditional Factor Statistical Arbitrage",
            "Strategy 7 — Skewness Parity Portfolio",
            "Strategy 9 — Robust Risk Parity With Fundamentals",
        ],
        "Strategy 5 — Conditional Factor Statistical Arbitrage": [
            "Chapter 8  Factor Investing Framework",
            "Chapter 9  Backtesting Philosophy And Common Pitfalls",
            "Quantmar Unified Specification",
            "Strategy 4 — Optimal Mean Reversion",
            "Strategy 7 — Skewness Parity Portfolio",
            "Strategy 9 — Robust Risk Parity With Fundamentals",
        ],
        "Strategy 7 — Skewness Parity Portfolio": [
            "Chapter 6  Return, Risk, And Portfolio Metrics",
            "Chapter 9  Backtesting Philosophy And Common Pitfalls",
            "Quantmar Unified Specification",
            "Strategy 4 — Optimal Mean Reversion",
            "Strategy 5 — Conditional Factor Statistical Arbitrage",
            "Strategy 9 — Robust Risk Parity With Fundamentals",
        ],
        "Strategy 9 — Robust Risk Parity With Fundamentals": [
            "Chapter 10  Risk Management Principles",
            "Chapter 9  Backtesting Philosophy And Common Pitfalls",
            "Quantmar Unified Specification",
            "Strategy 4 — Optimal Mean Reversion",
            "Strategy 5 — Conditional Factor Statistical Arbitrage",
            "Strategy 7 — Skewness Parity Portfolio",
        ],
        "Parametric Roll Detection  Enhancing Windmar With Academic Research": [
            "Windmar Project",
        ],
    }

    if title in cross_links:
        for link_title in cross_links[title]:
            if link_title in title_set and link_title not in see_also:
                see_also.append(link_title)

    return see_also


def process_page(
    page: dict,
    concept_patterns: list[tuple[re.Pattern, list[str]]],
    title_set: set[str],
    all_pages_by_title: dict,
) -> tuple[str, list[str], list[str]]:
    """Process a single page: insert inline links + see-also section.

    Returns (new_full_text, inline_links_added, see_also_added).
    """
    full_text = page["full_text"]
    title = page["title"]
    existing_links = page["existing_links"]
    inline_added: list[str] = []
    already_linked: set[str] = set(existing_links)

    # Split into frontmatter + body
    parts = full_text.split("---", 2)
    if len(parts) < 3:
        body = full_text
        frontmatter_prefix = ""
    else:
        frontmatter_prefix = parts[0] + "---" + parts[1] + "---"
        body = parts[2]

    # Remove existing "See also" section if present (we'll regenerate it)
    body = re.sub(
        r"\n---\n## See also\n(?:\s*-\s*\[\[[^\]]+\]\]\n?)*\s*$",
        "",
        body,
    )

    # Phase 1: Insert inline concept links
    for pat, target_titles in concept_patterns:
        for target_title in target_titles:
            if target_title == title:
                continue
            if target_title in already_linked:
                continue
            if target_title not in title_set:
                continue

            match = pat.search(body)
            if not match:
                continue

            result = insert_inline_link(body, match.start(), match.end() - match.start(), target_title)
            if result is not None:
                body = result
                already_linked.add(target_title)
                inline_added.append(target_title)

    # Phase 2: Add "See also" section
    see_also = get_see_also(page, title_set, all_pages_by_title)
    # Remove already-linked titles
    see_also = [t for t in see_also if t not in already_linked and t != title]

    see_also_text = ""
    if see_also:
        see_also_text = "\n---\n## See also\n"
        for sa_title in see_also:
            see_also_text += f"- [[{sa_title}]]\n"

    new_full = frontmatter_prefix + body.rstrip() + see_also_text
    if not new_full.endswith("\n"):
        new_full += "\n"

    return new_full, inline_added, see_also


def main() -> None:
    parser = argparse.ArgumentParser(description="Insert wiki-links to build knowledge graph")
    parser.add_argument("--execute", action="store_true", help="Apply changes (default: dry-run)")
    parser.add_argument("--data-dir", default=str(Path.home() / "katja"),
                        help="Katja data directory")
    args = parser.parse_args()

    pages_dir = Path(args.data_dir) / "pages"
    if not pages_dir.is_dir():
        print(f"ERROR: Pages directory not found: {pages_dir}")
        sys.exit(1)

    # Load all pages
    print("Loading pages...")
    all_pages = load_pages(pages_dir)
    print(f"  Loaded {len(all_pages)} pages")

    # Build indexes
    title_set = {p["title"] for p in all_pages if p["title"]}
    all_pages_by_title = {p["title"]: p for p in all_pages if p["title"]}
    linkable = [p for p in all_pages if is_linkable(p)]
    content_pages = [p for p in all_pages if is_content_page(p)]

    print(f"  Linkable targets: {len(linkable)}")
    print(f"  Content pages to process: {len(content_pages)}")

    # Build patterns
    concept_patterns = build_concept_patterns()
    print(f"  Concept patterns: {len(concept_patterns)}")

    # Process pages
    total_inline = 0
    total_see_also = 0
    pages_modified = 0
    results: list[tuple[str, list[str], list[str]]] = []

    for page in content_pages:
        new_text, inline_added, see_also_added = process_page(
            page, concept_patterns, title_set, all_pages_by_title,
        )

        if new_text != page["full_text"]:
            pages_modified += 1
            total_inline += len(inline_added)
            total_see_also += len(see_also_added)
            results.append((page["title"], inline_added, see_also_added))

            if args.execute:
                page["path"].write_text(new_text, encoding="utf-8")

    # Report
    print(f"\n{'='*60}")
    print(f"Wiki-Link Insertion Report")
    print(f"{'='*60}")
    print(f"  Pages modified: {pages_modified}")
    print(f"  Inline links added: {total_inline}")
    print(f"  See-also links added: {total_see_also}")
    print(f"  Total new links: {total_inline + total_see_also}")

    if results:
        print(f"\n--- Details ---")
        for title, inline, see_also in sorted(results, key=lambda x: -(len(x[1]) + len(x[2]))):
            total = len(inline) + len(see_also)
            print(f"\n  {title[:70]}")
            if inline:
                print(f"    Inline ({len(inline)}):")
                for link in inline:
                    print(f"      + [[{link[:60]}]]")
            if see_also:
                print(f"    See also ({len(see_also)}):")
                for link in see_also:
                    print(f"      + [[{link[:60]}]]")

    if not args.execute:
        print(f"\n[DRY RUN] No changes made. Use --execute to apply.\n")
    else:
        print(f"\nDone! Restart the app to rebuild the index: docker compose restart app\n")


if __name__ == "__main__":
    main()
