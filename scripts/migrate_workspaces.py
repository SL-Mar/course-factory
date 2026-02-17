#!/usr/bin/env python3
"""One-time migration: classify 354 pages into 11 workspaces by title keywords.

Usage:
    python scripts/migrate_workspaces.py               # dry-run (default)
    python scripts/migrate_workspaces.py --execute      # apply changes

Can run inside Docker:
    docker compose exec app python /app/scripts/migrate_workspaces.py --execute
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path


# ── Workspace definitions: (name, icon, color, keywords) ──

WORKSPACES = [
    {
        "name": "admin",
        "icon": "folder",
        "color": "#d97706",
        "keywords": [r"\d+ euros", r"subscriptions", r"hospital", r"ospedale"],
    },
    {
        "name": "zvezda",
        "icon": "anchor",
        "color": "#0891b2",
        "keywords": [
            r"hull", r"drydock", r"keel", r"cabin", r"lifejacket",
            r"primer", r"rudder", r"antifouling", r"propeller",
            r"starboard", r"mooring", r"sanitary", r"locker",
            r"sewage", r"piping", r"stretch cable", r"zvezda",
            r"aft cabin", r"cargo issues",
        ],
    },
    {
        "name": "windmar",
        "icon": "wind",
        "color": "#059669",
        "keywords": [
            r"windmar", r"spec p\d", r"maritime os", r"\bais\b",
            r"\bera5\b", r"gisis", r"seakeeping", r"sbg ellipse",
            r"wasserstein", r"route strip", r"weather visual",
            r"hydrodynamique", r"monte carlo param", r"enveloppe exp",
            r"shipboard os", r"copernicusmarine",
        ],
    },
    {
        "name": "quantmar",
        "icon": "chart-line",
        "color": "#4f46e5",
        "keywords": [
            r"quantmar", r"strategy \d", r"backtest",
            r"mean reversion", r"factor.*arbitrage",
            r"skewness parity", r"risk parity.*fundamentals",
            r"quant neo", r"quantfundamentals",
        ],
    },
    {
        "name": "marchat",
        "icon": "comment-dots",
        "color": "#7c3aed",
        "keywords": [
            r"marchat", r"\bsolas\b", r"\bstcw\b",
            r"maritime legal", r"maritime rag",
        ],
    },
    {
        "name": "amphitrite",
        "icon": "sailboat",
        "color": "#0d9488",
        "keywords": [r"amphitrite"],
    },
    {
        "name": "development",
        "icon": "code",
        "color": "#2383e2",
        "keywords": [
            r"\bclaude\b", r"cli.first", r"course factory",
            r"building your own", r"agentic ai", r"development ideas",
            r"building an ai.native", r"virtual software engineer",
            r"typescript crash", r"start.up strategy",
        ],
    },
    {
        "name": "marine-issues",
        "icon": "screwdriver-wrench",
        "color": "#dc2626",
        "keywords": [
            r"\bmiros\b", r"marine osint", r"shipboard",
        ],
    },
    {
        "name": "articles",
        "icon": "newspaper",
        "color": "#be185d",
        "keywords": [
            r"article", r"\bdcr\b", r"distance.*criticality",
            r"shared lora", r"ml research", r"continual learning",
            r"publication roadmap", r"alpha discovery",
            r"seven years to one",
        ],
    },
    {
        "name": "q2c",
        "icon": "book-open",
        "color": "#65a30d",
        "keywords": [
            r"chapter \d", r"module \d", r"part \d",
            r"capstone",
        ],
    },
    {
        "name": "trading",
        "icon": "arrow-trend-up",
        "color": "#ea580c",
        "keywords": [
            r"\bgold\b", r"\bsilver\b", r"\bxau\b", r"\bxag\b",
            r"pre.market", r"breakout", r"saturday trading",
            r"trading ideas", r"trading call",
            r"eur.usd", r"eur.jpy", r"eur.gbp", r"usd.jpy",
            r"potential breakout", r"training datasets",
            # Known ticker pages
            r"^asts", r"^avdx", r"^cflt", r"^dlo$", r"^egan$",
            r"^eric$", r"^imxi$", r"^indi$", r"^kopn$",
            r"^kspi", r"^laes", r"^lpth", r"^nndm$",
            r"^ntgr", r"^nvts", r"^odd", r"^poet", r"^powi",
            r"^pubm$", r"^rekr$", r"^veri", r"^alab$",
        ],
    },
]

# Compile patterns once
for ws in WORKSPACES:
    ws["_patterns"] = [re.compile(kw, re.IGNORECASE) for kw in ws["keywords"]]


def classify(title: str) -> str | None:
    """Return workspace name for a title, or None if no match."""
    for ws in WORKSPACES:
        for pat in ws["_patterns"]:
            if pat.search(title):
                return ws["name"]
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate pages into workspaces")
    parser.add_argument("--execute", action="store_true", help="Apply changes (default: dry-run)")
    parser.add_argument("--data-dir", default=str(Path.home() / "katja"),
                        help="Katja data directory")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    pages_dir = data_dir / "pages"
    db_path = data_dir / "data" / "katja.db"

    if not pages_dir.is_dir():
        print(f"ERROR: Pages directory not found: {pages_dir}")
        sys.exit(1)

    # ── Phase 1: Classify pages by reading frontmatter titles ──

    assignments: dict[str, tuple[str, str]] = {}  # page_id -> (new_workspace, title)
    unmatched: list[tuple[str, str]] = []

    for md_file in sorted(pages_dir.glob("*.md")):
        page_id = md_file.stem
        text = md_file.read_text(encoding="utf-8", errors="replace")

        # Extract title from YAML frontmatter
        title_match = re.search(r"^title:\s*['\"]?(.+?)['\"]?\s*$", text, re.MULTILINE)
        if not title_match:
            continue
        title = title_match.group(1).strip()

        ws = classify(title)
        if ws:
            assignments[page_id] = (ws, title)
        else:
            unmatched.append((page_id, title))

    # ── Phase 2: Report ──

    ws_counts: dict[str, int] = {}
    for ws_name, _title in assignments.values():
        ws_counts[ws_name] = ws_counts.get(ws_name, 0) + 1

    print("\n=== Workspace Migration Report ===\n")
    for ws in WORKSPACES:
        count = ws_counts.get(ws["name"], 0)
        print(f"  {ws['icon']}  {ws['name']:<16} {count:>3} pages")
    print(f"\n  {'':2}  {'default':<16} {len(unmatched):>3} pages (unmatched)")
    print(f"\n  Total classified: {len(assignments)}")
    print(f"  Total unmatched:  {len(unmatched)}")
    print(f"  Total files:      {len(assignments) + len(unmatched)}")

    if not args.execute:
        print("\n[DRY RUN] No changes made. Use --execute to apply.\n")

        # Show first 5 unmatched for review
        if unmatched:
            print("Sample unmatched titles:")
            for pid, t in unmatched[:10]:
                print(f"  - {t}")
        return

    # ── Phase 3: Update frontmatter in .md files ──

    updated = 0
    for page_id, (ws_name, title) in assignments.items():
        md_file = pages_dir / f"{page_id}.md"
        text = md_file.read_text(encoding="utf-8", errors="replace")

        # Replace workspace field in YAML frontmatter
        new_text, n = re.subn(
            r"^workspace:\s*.*$",
            f"workspace: {ws_name}",
            text,
            count=1,
            flags=re.MULTILINE,
        )
        if n == 0:
            # No workspace field — insert after title
            new_text = re.sub(
                r"^(title:\s*.+)$",
                rf"\1\nworkspace: {ws_name}",
                text,
                count=1,
                flags=re.MULTILINE,
            )

        md_file.write_text(new_text, encoding="utf-8")
        updated += 1

    print(f"\nUpdated {updated} .md files.")

    # ── Phase 4: Seed workspace_meta table ──

    if db_path.is_file():
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workspace_meta (
                name TEXT PRIMARY KEY,
                icon TEXT DEFAULT '',
                color TEXT DEFAULT '#2383e2',
                sort_order INTEGER DEFAULT 0
            )
        """)
        for i, ws in enumerate(WORKSPACES):
            conn.execute(
                "INSERT OR REPLACE INTO workspace_meta (name, icon, color, sort_order) VALUES (?,?,?,?)",
                (ws["name"], ws["icon"], ws["color"], i),
            )
        conn.commit()
        conn.close()
        print(f"Seeded {len(WORKSPACES)} workspace_meta entries in SQLite.\n")
    else:
        print(f"WARNING: DB not found at {db_path} — workspace_meta not seeded.\n")
        print("The table will be seeded on next app startup when the index rebuilds.\n")

    print("Done! Restart the app to rebuild the index: docker compose restart app\n")


if __name__ == "__main__":
    main()
