# Katja

Local-first knowledge operating system — your brain's OS, running on your machine.

## What It Does

Katja is a self-hosted knowledge management platform that stores everything as
plain markdown files with YAML frontmatter. It features bidirectional wiki-links,
semantic search via vector embeddings, an AI assistant, and a clean minimalist UI.

## Architecture

- **Storage**: Flat markdown files with YAML frontmatter, ULID-named
- **Metadata**: SQLite (WAL mode) — page index, backlinks, engine runs, table registry
- **Vector search**: Qdrant + nomic-embed-text (Ollama embeddings)
- **LLM**: Ollama (local) + Anthropic + OpenAI (cloud fallback)

## Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite
- **Backend**: FastAPI, Pydantic
- **LLMs**: Ollama (local), Anthropic, OpenAI
- **Search**: Qdrant (vectors), SQLite (metadata)
- **License**: Ed25519 (NaCl) offline validation
- **Config**: Pydantic settings with YAML overlay (`~/.config/katja/config.yaml`)

## CLI

```bash
katja version                       # Print version
katja serve                         # Start the server
katja reindex                       # Rebuild metadata index
katja keygen init                   # Generate Ed25519 keypair
katja keygen generate <email> <product> --tier <tier> --days <days>
katja keygen validate <key>         # Validate license signature
katja config init                   # Create default YAML config
katja config show                   # Display config (secrets masked)
```

## Running

```bash
# Install
pip install -e .

# Start the server
katja serve

# Or with Docker
docker compose up -d
```

The frontend is bundled into the FastAPI static files at build time.
Access the UI at `http://localhost:8000`.

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
