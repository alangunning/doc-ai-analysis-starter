---
title: Configuration
sidebar_position: 2
---

# Configuration

Doc AI Starter uses environment variables to control models and GitHub Actions. Copy `.env.example` to `.env` and edit as needed. Variables in your shell override values in the file. The CLI ensures the `.env` file has `0600` permissions when creating or updating it.

### Precedence

When the same setting is defined in multiple places the resolution order is:

1. Command-line flags
2. Shell environment variables
3. Values from `.env`
4. Built-in defaults in code or prompt files

## API Keys and Endpoints

Set `GITHUB_TOKEN` with the **Models:read** scope to access GitHub Models at
`https://models.github.ai/inference`. All helpers read `BASE_MODEL_URL` for the
API endpoint. If `BASE_MODEL_URL` targets GitHub Models (or is unset), the
validator switches to OpenAI's `https://api.openai.com/v1` endpoint and expects
`OPENAI_API_KEY`. Use `BASE_MODEL_URL` or per-step overrides such as
`VECTOR_BASE_MODEL_URL` to point individual stages at a different provider.

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
