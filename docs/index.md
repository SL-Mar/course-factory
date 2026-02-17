# Katja

**Katja** is a local-first knowledge operating system. It stores everything as
plain markdown files with YAML frontmatter, features bidirectional wiki-links,
semantic search via vector embeddings, an AI assistant, and a clean minimalist UI.

---

## Quick Start

```bash
pip install -e .
katja version
```

You should see the installed version printed to the terminal, confirming that
the CLI is available.

### First-time setup

```bash
# Generate a license keypair
katja keygen init

# Create a default configuration file
katja config init
```

Once configured, launch the server:

```bash
katja serve
```

---

## Next Steps

- [Getting Started](getting-started.md) -- full installation and first-run walkthrough
- [Configuration](configuration.md) -- environment variables and YAML options
- [API Reference](api.md) -- REST API documentation
