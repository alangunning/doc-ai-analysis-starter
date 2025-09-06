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
- `show prompt <doc-type> [--topic <name>]` – print the prompt definition for a document type
- `show doc-types` – list discovered document types under the `data/` directory
- `show topics` – list analysis topics inferred from prompt files
- `edit prompt <doc-type> [--topic <name>]` – open the prompt file in `$EDITOR` (falls back to `vi`/`nano`)
- `new doc-type <name>` – scaffold a document type and save an optional description
- `new topic <doc-type> <name>` – create a topic prompt with an optional description
- `new rename-doc-type <old> <new>` – rename a document type and its prompts
- `new delete-doc-type <name>` – remove a document type directory
- `new rename-topic <doc-type> <old> <new>` – rename a topic prompt
- `new delete-topic <doc-type> <name>` – delete a topic prompt
- `pipeline` – convert, validate, analyze and embed supported raw documents in a directory; paths containing `.converted` are ignored

  Use `--workers N` to process documents concurrently. Control which steps run with
  `--resume-from` or `--skip`.

  The `analyze` and `pipeline` commands accept `--topic` to run one or more
  topic-specific prompts. When no topic is supplied, the CLI searches for
  prompt files matching `analysis_<topic>.prompt.yaml` or
  `*.analysis.<topic>.prompt.yaml` and writes results to
  `<doc>.analysis.<topic>.json`.

  Use `--workers N` to process documents concurrently.
- `version` – show the installed package version

By default, the `pipeline` command only processes files with extensions supported by Docling (e.g., `.pdf`) and skips any path containing `.converted` to avoid re-processing generated outputs.

Many commands accept a `--force` flag to bypass metadata checks and re-run steps even if they were previously completed.

Pass `--model` and `--base-model-url` to relevant commands to override model selection. Logging flags `--verbose`, `--log-level` and `--log-file` may be placed either before or after subcommands and all commands honour them. For example:

```bash
doc-ai --log-level INFO convert report.pdf
doc-ai analyze report.md --log-file analysis.log
doc-ai analyze report.md --topic finance --topic risk
```

`--verbose` is a shortcut for `--log-level DEBUG`.

`doc_ai/cli.py` provides an executable entry point so the interface can be invoked directly:

```bash
python doc_ai/cli.py convert report.pdf --format markdown
```

After installation, the same commands are available via the `doc-ai` console script. Run `doc-ai` with no arguments to enter an interactive shell.

## Global configuration and logging

The CLI looks for a global configuration file in the user config directory provided by `platformdirs` (for example `~/.config/doc_ai/config.json` on Linux). Use `doc-ai config --global set VAR=VALUE` to persist settings across projects. Command-line flags take precedence, followed by environment variables, entries in a project `.env` file and finally values from the global config. Built-in defaults apply only if a setting is absent from all other sources.

Set `LOG_LEVEL` or `LOG_FILE` in any config source or pass `--log-level` / `--log-file` on the command line to tweak logging behavior.
Matching OpenAI or GitHub tokens are masked in log output, preserving only the first and last four characters.
