---
title: CLI Module
sidebar_position: 2
---

# CLI Module

The `doc_ai.cli` package provides a Typer-based command line interface for orchestrating the document workflow. It reads defaults from environment variables (and a local `.env` file) and exposes subcommands for each major step. Running `doc-ai` with no arguments launches an interactive shell powered by [click-repl](https://github.com/click-contrib/click-repl) with tab completion and command history.

## Global options

The CLI supports a few global flags that apply to every command:

- `--config PATH` – load settings from an explicit TOML file; if omitted the CLI searches `.doc-ai.toml`, `~/.config/doc-ai/config.toml`, then `/etc/doc-ai/config.toml`.
- `--log-level [critical|error|warning|info|debug]` – set logging verbosity.
- `--log-file PATH` – write detailed logs to a file.

## Commands

- `config` – show or update runtime configuration
- `convert` – run Docling to convert raw documents into text formats
- `validate` – compare a converted file with its source using an AI model
- `analyze` – execute an analysis prompt against a Markdown document
- `embed` – generate vector embeddings for Markdown files
- `pipeline` – convert, validate, analyze and embed supported raw documents in a directory; paths containing `.converted` are ignored
  By default, the `pipeline` command only processes files with extensions supported by Docling (e.g., `.pdf`) and skips any path containing `.converted` to avoid re-processing generated outputs.

Pass `--model` and `--base-model-url` to relevant commands to override model selection.

### Help output

```bash
$ doc-ai --help
Usage: doc-ai [OPTIONS] COMMAND [ARGS]...

Options:
  --config PATH   Read settings from PATH  [default: ~/.config/doc-ai/config.toml]
  --log-level [critical|error|warning|info|debug]
                  Set log verbosity
  --log-file PATH  Write log output to PATH
  --help          Show this message and exit.

Commands:
  config
  convert
  validate
  analyze
  embed
  pipeline
```

`doc_ai/cli.py` provides an executable entry point so the interface can be invoked directly for scripting. After installation, the same commands are available via the `doc-ai` console script or the interactive shell.
