# Course Factory

An autonomous system that transforms technical knowledge into structured courses.
It ingests source material (GitHub repos, web pages, Notion pages), runs it through
a multi-stage LLM pipeline, and produces slide decks ready for presentation.

## What It Does

You give it a topic and source material. It produces a complete course: outline,
research notes, lesson scripts, and Marp slide decks -- all generated through
a sequence of LLM calls with no manual intervention between stages.

**Pipeline stages:**

| Stage | Directory | What happens |
|-------|-----------|--------------|
| Knowledge | `01-knowledge/` | Fetches content from GitHub repos, URLs, and Notion pages. Saves as Markdown. |
| Discovery | `02-discovery/` | LLM generates a course proposal and structured outline (modules + lessons). |
| Research | `03-research/` | LLM produces per-module research notes from ingested sources. |
| Synthesis | `04-synthesis/` | LLM writes per-lesson scripts from the research notes. |
| Production | `05-production/` | LLM converts lesson scripts into Marp slide decks (`.marp.md`). |

Three additional stages (Media, QA, Publish) exist as placeholders in the codebase.

## Interface

A web UI (React + FastAPI) serves as the primary interface:

- **Setup wizard** -- Configure LLM providers, test connections (Ollama, PostgreSQL,
  Qdrant, Redis, Telegram), validate license key
- **Dashboard** -- Create courses, define source material (GitHub repos, URLs, Notion pages)
- **Workspace** -- File tree explorer, stage runner with real-time progress,
  Markdown viewer, Marp slide preview with 16:9 cards, inline file editor,
  token usage tracking

The workspace stores all generated content on disk at
`~/.config/course-factory/workspaces/<course-id>/`.

## CLI

```bash
cf version                          # Print version
cf keygen init                      # Generate Ed25519 keypair
cf keygen generate <email> <product> --tier <tier> --days <days>
cf keygen validate <key>            # Validate license signature
cf config init                      # Create default YAML config
cf config show                      # Display config (secrets masked)
```

## LLM Router

Task-aware model selection with automatic VRAM management:

- **Local**: Ollama (qwen2.5:14b default) -- ensures only one model loaded at a time
- **Cloud**: Anthropic Claude and OpenAI as configured fallbacks
- Per-task model override via config
- Token tracking per stage, persisted to `_tokens.json` per course

## Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite
- **Backend**: FastAPI, Pydantic, SQLAlchemy + Alembic
- **LLMs**: Ollama (local), Anthropic, OpenAI
- **Database**: PostgreSQL (TimescaleDB), Qdrant (vectors), Redis (cache)
- **License**: Ed25519 (NaCl) offline validation
- **Config**: Pydantic settings with YAML overlay (`~/.config/course-factory/config.yaml`)
- **Slides**: Marp markdown format, viewable with `marp-cli`

## Running

```bash
# Install
pip install -e .

# Generate license keypair
cf keygen init

# Create config
cf config init

# Start the stack
docker compose up -d

# Or run the API server directly
uvicorn course_factory.api.main:app --host 0.0.0.0 --port 8000
```

The frontend is bundled into the FastAPI static files at build time.
Access the UI at `http://localhost:8000`.

## Viewing Slides

The generated `.marp.md` files in `05-production/` can be presented with Marp CLI:

```bash
# Preview in browser
npx @marp-team/marp-cli -p lesson.marp.md

# Export to HTML, PDF, or PowerPoint
npx @marp-team/marp-cli lesson.marp.md -o lesson.html
npx @marp-team/marp-cli lesson.marp.md -o lesson.pdf
npx @marp-team/marp-cli lesson.marp.md -o lesson.pptx
```

## License

Apache 2.0 -- see [LICENSE](LICENSE) for details.
