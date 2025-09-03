---
title: CLI Module
sidebar_position: 2
---

# CLI Module

The `doc_ai.cli` package provides a Typer-based command line interface for orchestrating the document workflow. It reads defaults from environment variables (and a local `.env` file) and exposes subcommands for each major step.

## Commands

- `config` – show or update runtime configuration
- `convert` – run Docling to convert raw documents into text formats
- `validate` – compare a converted file with its source using an AI model
- `analyze` – execute an analysis prompt against a Markdown document
- `embed` – generate vector embeddings for Markdown files
- `pipeline` – convert, validate, analyze and embed an entire directory

Pass `--model` and `--base-model-url` to relevant commands to override model selection. Add `--verbose` for debug logging.

`doc_ai/cli.py` provides an executable entry point so the interface can be invoked directly:

```bash
python doc_ai/cli.py convert report.pdf --format markdown
```

After installation, the same commands are available via the `doc-ai` console script.
