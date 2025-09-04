---
title: CLI Module
sidebar_position: 2
---

# CLI Module

The `doc_ai.cli` package provides a Typer-based command line interface for orchestrating the document workflow. It reads defaults from a platform-specific **global config file**, a project `.env` file and environment variables, then exposes subcommands for each major step. Each command lives in its own module within `doc_ai.cli` and is registered with the top-level app.

## Commands

- `config` – manage runtime configuration
- `config show` – display current settings
- `config set` – update environment variables
- `convert` – run Docling to convert raw documents into text formats
- `validate` – compare a converted file with its source using an AI model
- `analyze` – execute an analysis prompt against a Markdown document
- `embed` – generate vector embeddings for Markdown files
- `pipeline` – convert, validate, analyze and embed supported raw documents in a directory; paths containing `.converted` are ignored
By default, the `pipeline` command only processes files with extensions supported by Docling (e.g., `.pdf`) and skips any path containing `.converted` to avoid re-processing generated outputs.

Pass `--model` and `--base-model-url` to relevant commands to override model selection. Global options `--log-level` and `--log-file` control logging output, and `--verbose` is a shortcut for `--log-level DEBUG`.

`doc_ai/cli.py` provides an executable entry point so the interface can be invoked directly:

```bash
python doc_ai/cli.py convert report.pdf --format markdown
```

After installation, the same commands are available via the `doc-ai` console script. Run `doc-ai` with no arguments to enter an interactive shell.

## Global configuration and logging

The CLI looks for a global configuration file in the user config directory provided by `platformdirs` (for example `~/.config/doc_ai/config.json` on Linux). Use `doc-ai config --global set VAR=VALUE` to persist settings across projects. Command-line flags override environment variables, which in turn override `.env` entries and finally values in the global config file.

Set `LOG_LEVEL` or `LOG_FILE` in any config source or pass `--log-level` / `--log-file` on the command line to tweak logging behavior.
