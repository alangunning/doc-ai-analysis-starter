---
title: Configuration
sidebar_position: 6
---

# Configuration

Doc AI Starter uses environment variables to control models and GitHub Actions. Copy `.env.example` to `.env` and edit as needed. Variables in your shell override values in the file.

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

## Model Base URLs

By default the helpers call GitHub's public models at `https://models.github.ai/inference`. To use a different endpoint, set one of the following variables:

| Variable | Purpose |
| --- | --- |
| `BASE_MODEL_URL` | Default for all modules |
| `ANALYZE_BASE_MODEL_URL` | Analysis prompts |
| `VALIDATE_BASE_MODEL_URL` | Output validation |
| `PR_REVIEW_BASE_MODEL_URL` | Pull request reviews |
| `VECTOR_BASE_MODEL_URL` | Embedding generation |

Example override:

```env
BASE_MODEL_URL=https://models.mycompany.example/inference
```

## Model Defaults

You can also override the model used for each module. The `.env.example` file lists the available variables such as `PR_REVIEW_MODEL`, `VALIDATE_MODEL`, `ANALYZE_MODEL`, and `EMBED_MODEL`.
