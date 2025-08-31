---
title: Environment Variables
sidebar_position: 4
---

# Environment Variables

Settings live in a `.env` file at the repository root. Copy `.env.example` to
`.env` and adjust values as needed. Variables defined by the runtime (e.g., CI
secrets) override values in the file.

## Docs site configuration

- `DOCS_SITE_URL` – base site URL such as `https://alangunning.github.io`
- `DOCS_BASE_URL` – path where the docs are served
- `GITHUB_ORG` / `GITHUB_REPO` – GitHub owner and repository name

## Model overrides

Uncomment entries to change which model each script or workflow uses.

- `PR_REVIEW_MODEL`
- `VALIDATE_MODEL`
- `ANALYZE_MODEL`
- `EMBED_MODEL`
- `EMBED_DIMENSIONS` – required when the embedding model uses custom dimensions

## Base model URLs

Point to self-hosted model endpoints instead of the default GitHub Models URL.

- `PR_REVIEW_BASE_MODEL_URL`
- `VALIDATE_BASE_MODEL_URL`
- `ANALYZE_BASE_MODEL_URL`

## Conversion formats

`OUTPUT_FORMATS` lists comma-separated formats produced by `convert.py`.
Supported values: `markdown`, `html`, `json`, `text`, `doctags`.

## Workflow toggles

Set `DISABLE_ALL_WORKFLOWS=true` to skip all automation. Individual workflows
can be enabled or disabled with `ENABLE_*` variables, for example:

- `ENABLE_CONVERT_WORKFLOW`
- `ENABLE_VALIDATE_WORKFLOW`
- `ENABLE_VECTOR_WORKFLOW`
- `ENABLE_PROMPT_ANALYSIS_WORKFLOW`
- `ENABLE_PR_REVIEW_WORKFLOW`
- `ENABLE_DOCS_WORKFLOW`
- `ENABLE_LINT_WORKFLOW`
- `ENABLE_AUTO_MERGE_WORKFLOW`

Refer to `.env.example` for a complete list of options.
