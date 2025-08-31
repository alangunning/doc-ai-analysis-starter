---
sidebar_position: 2
---

# Setup

## Requirements

- Python >= 3.10
- Environment variables such as `GITHUB_TOKEN` for model access and GitHub CLI operations (see `.env.example`).

Create a `.env` file based on `.env.example` and supply your token (and optional settings). Environment variables provided by the runtime (for example via GitHub Secrets) override values in the file, allowing cloud agents to inject `GITHUB_TOKEN` automatically. Each workflow's model can be overridden by setting `PR_REVIEW_MODEL`, `VALIDATE_MODEL`, `ANALYZE_MODEL`, or `EMBED_MODEL`.

Set `DISABLE_ALL_WORKFLOWS=true` in the `.env` file to skip every GitHub Action without editing workflow files. Individual workflows remain disabled unless explicitly enabled with variables like `ENABLE_CONVERT_WORKFLOW`, `ENABLE_VALIDATE_WORKFLOW`, `ENABLE_VECTOR_WORKFLOW`, `ENABLE_PROMPT_ANALYSIS_WORKFLOW`, `ENABLE_PR_REVIEW_WORKFLOW`, `ENABLE_DOCS_WORKFLOW`, `ENABLE_AUTO_MERGE_WORKFLOW`, or `ENABLE_LINT_WORKFLOW`.

## Installation

```bash
pip install -e .
```

### Docs site

```bash
cd docs
npm install
npm run build
```
