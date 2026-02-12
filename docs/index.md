# Course Factory

**Course Factory** is an autonomous agentic system that transforms technical
knowledge into publishable, structured courses. It ingests source material
(papers, docs, codebases), orchestrates LLM-driven research and synthesis, and
produces multi-format course content ready for distribution.

---

## Quick Start

```bash
pip install -e .
cf version
```

You should see the installed version printed to the terminal, confirming that
the CLI is available.

### First-time setup

```bash
# Generate a license keypair
cf keygen init

# Create a default configuration file
cf config init
```

Once configured, launch a pipeline run with:

```bash
cf run --topic "Your Topic Here"
```

---

## Next Steps

- [Getting Started](getting-started.md) -- full installation and first-run walkthrough
- [Configuration](configuration.md) -- environment variables and YAML options
- [Pipeline Stages](stages.md) -- detailed breakdown of stages 0-7
- [API Reference](api.md) -- REST API documentation
