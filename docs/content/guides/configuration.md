---
title: Configuration
sidebar_position: 2
---

# Configuration

Doc AI Starter uses environment variables and configuration files to control models and GitHub Actions. Copy `.env.example` to `.env` and edit as needed. Variables in your shell override values in the file. The CLI ensures the `.env` file has `0600` permissions when creating or updating it. It also reads a **global configuration file** in `platformdirs`' user config directory (e.g. `~/.config/doc_ai/config.json`) for settings that apply across projects.

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
Secrets that resemble OpenAI or GitHub tokens are partially masked in logs, keeping the first and last four characters and replacing the middle with `*`.
