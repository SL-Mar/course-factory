# Course Factory

An autonomous agentic system that transforms technical knowledge into
publishable, structured courses. Course Factory ingests source material,
orchestrates multi-model LLM pipelines, and produces polished course content
end-to-end -- from discovery through quality assurance to publication.

## Features

- **License System** -- Ed25519 keypair generation and offline license validation
- **LLM Router** -- Task-aware model selection across Ollama providers with automatic fallback
- **Pipeline Engine** -- Deterministic, resumable pipeline with checkpoint/recovery
- **Multi-Stage Processing** -- Eight discrete stages (0-7) from discovery to publishing
- **Knowledge Layer** -- Qdrant vector store integration for semantic retrieval
- **REST API** -- FastAPI service for pipeline control and monitoring
- **TUI Dashboard** -- Terminal UI for real-time pipeline observation
- **Docker Ready** -- Full Docker Compose stack with TimescaleDB

## Quick Start

```bash
# Install in development mode
pip install -e .

# Verify the CLI
cf version

# Generate a license keypair
cf keygen init

# Create default configuration
cf config init

# Launch a pipeline run
cf run --topic "Your Topic Here"
```

## Architecture

Course Factory processes content through eight pipeline stages:

| Stage | Name        | Description                              |
|-------|-------------|------------------------------------------|
| 0     | Discovery   | Identify and collect source material     |
| 1     | Research    | Deep analysis of collected sources       |
| 2     | Synthesis   | Structure knowledge into course outline  |
| 3     | Production  | Generate lesson content and exercises    |
| 4     | Media       | Create diagrams, figures, and assets     |
| 5     | QA          | Automated quality and accuracy checks    |
| 6     | Publish     | Render final output (PDF, HTML, SCORM)   |
| 7     | Notify      | Deliver completion notifications         |

Each stage is independently resumable; a failed run picks up exactly where it
left off.

## Docker

```bash
# Start the full stack (TimescaleDB + app)
docker compose up -d

# Or build and run the CLI image directly
docker build -t course-factory .
docker run --rm course-factory version
```

## Configuration

Course Factory reads configuration from `cf.yml` (or environment variables
prefixed with `CF_`). Run `cf config init` to generate a starter file with
all available options documented inline.

## License

Apache 2.0 -- see [LICENSE](LICENSE) for details.
