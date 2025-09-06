---
title: Configuration
sidebar_position: 2
---

# Configuration

Doc AI Starter uses environment variables and configuration files to control models and GitHub Actions. Copy `.env.example` to `.env` and edit as needed. Variables in your shell override values in the file, the project `.env` overrides the global configuration file, and command-line flags trump them all. The CLI ensures the `.env` file has `0600` permissions when creating or updating it. It also reads a **global configuration file** in `platformdirs`' user config directory (e.g. `~/.config/doc_ai/config.json`) for settings that apply across projects. Use `doc-ai config set VAR=VALUE` or `doc-ai config toggle KEY` to update these settings.

Run `doc-ai config wizard` to step through common options interactively.

### Precedence

When the same setting is defined in multiple places the resolution order is:

1. Command-line flags
2. Shell environment variables
3. Values from `.env`
4. Values from the global config file
5. Built-in defaults in code or prompt files

## API Keys and Endpoints

Set `GITHUB_TOKEN` with the **Models:read** scope to access GitHub Models at
`https://models.github.ai/inference`. All helpers read `BASE_MODEL_URL` for the
API endpoint. The validation step requires OpenAI's file inputs, so provide
`OPENAI_API_KEY` and, if needed, `VALIDATE_BASE_MODEL_URL=https://api.openai.com/v1`
(this is the CLI default) while other steps can remain on the provider specified
by `BASE_MODEL_URL`.

## Workflow Toggles

Each GitHub Action can be enabled or disabled individually. Set the variable to `true` or `false`:

| Variable | Workflow |
| --- | --- |
| `ENABLE_CONVERT_WORKFLOW` | Convert documents |
| `ENABLE_VALIDATE_WORKFLOW` | Validate outputs |
| `ENABLE_PROMPT_ANALYSIS_WORKFLOW` | Run analysis prompts |
| `ENABLE_VECTOR_WORKFLOW` | Generate vector embeddings |
| `ENABLE_PR_REVIEW_WORKFLOW` | Review pull requests |
| `ENABLE_DOCS_WORKFLOW` | Build documentation site |
| `ENABLE_AUTO_MERGE_WORKFLOW` | Auto merge pull requests |
| `ENABLE_LINT_WORKFLOW` | Run lint checks |

Set `DISABLE_ALL_WORKFLOWS=true` to skip every workflow regardless of the individual toggles.

## Model Defaults

You can also override the model used for each module. The `.env.example` file lists the available variables such as `PR_REVIEW_MODEL`, `VALIDATE_MODEL`, `ANALYZE_MODEL`, and `EMBED_MODEL`.

## Logging

Set `LOG_LEVEL` or `LOG_FILE` in any configuration source to control logging. The CLI accepts matching `--log-level` and `--log-file` options to override these values for a single run, and `--verbose` acts as a shortcut for `--log-level DEBUG`.

## CLI Option Environment Variables

Many command options can also be configured through environment variables or entries in `.env` and the global config file. The table below lists the mapping between CLI flags and their corresponding variables:

| Command | Option | Environment variable |
| --- | --- | --- |
| `doc-ai analyze` | `--model` | `MODEL` |
| `doc-ai analyze` | `--base-model-url` | `BASE_MODEL_URL` |
| `doc-ai analyze` | `--require-structured` | `REQUIRE_STRUCTURED` |
| `doc-ai analyze` | `--show-cost` | `SHOW_COST` |
| `doc-ai analyze` | `--estimate` | `ESTIMATE` |
| `doc-ai analyze` | `--force` | `FORCE` |
| `doc-ai analyze` | `--fail-fast` | `FAIL_FAST` |
| `doc-ai convert` | `--format` | `OUTPUT_FORMATS` |
| `doc-ai convert` | `--force` | `FORCE` |
| `doc-ai embed` | `--fail-fast` | `FAIL_FAST` |
| `doc-ai embed` | `--workers` | `WORKERS` |
| `doc-ai init-workflows` | `--dest` | `DEST` |
| `doc-ai init-workflows` | `--overwrite` | `OVERWRITE` |
| `doc-ai init-workflows` | `--dry-run` | `DRY_RUN` |
| `doc-ai init-workflows` | `--yes` | `YES` |
| `doc-ai pipeline` | `--format` | `OUTPUT_FORMATS` |
| `doc-ai pipeline` | `--model` | `MODEL` |
| `doc-ai pipeline` | `--base-model-url` | `BASE_MODEL_URL` |
| `doc-ai pipeline` | `--fail-fast` | `FAIL_FAST` |
| `doc-ai pipeline` | `--show-cost` | `SHOW_COST` |
| `doc-ai pipeline` | `--estimate` | `ESTIMATE` |
| `doc-ai pipeline` | `--workers` | `WORKERS` |
| `doc-ai pipeline` | `--force` | `FORCE` |
| `doc-ai pipeline` | `--dry-run` | `DRY_RUN` |
| `doc-ai pipeline` | `--resume-from` | `RESUME_FROM` |
| `doc-ai query` | `--ask` | `ASK` |
| `doc-ai query` | `--model` | `MODEL` |
| `doc-ai validate` | `--model` | `VALIDATE_MODEL` |
| `doc-ai validate` | `--base-model-url` | `VALIDATE_BASE_MODEL_URL` |
| `doc-ai validate` | `--force` | `FORCE` |
| Global | `--log-level` | `LOG_LEVEL` |
| Global | `--log-file` | `LOG_FILE` |
| Global | `--verbose` | `VERBOSE` |
| Global | `--banner/--quiet` | `DOC_AI_BANNER` |

Secrets that resemble OpenAI or GitHub tokens are partially masked in logs, keeping the first and last four characters and replacing the middle with `*`.
