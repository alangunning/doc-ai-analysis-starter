# AI Agent Prompt: Recreate `doc-ai-analysis-starter`

You are an AI coding agent with access to a Bash shell and GitHub CLI. Rebuild
this repository **without cloning or downloading any remote template**.
All file contents required to recreate the project are included below.
Follow the steps exactly and stop on any error.

## Steps
1. Create and initialize a new repository:
   ```bash
   mkdir NEW_REPO
   cd NEW_REPO
   git init -b main
   ```
2. Reproduce the directory tree:
   ```bash
   mkdir -p data outputs prompts scripts docai/github docai/metadata docs/docs docs/src/css .github/workflows docs/build
   touch data/.gitkeep outputs/.gitkeep docs/build/.gitkeep
   ```
3. For each file path listed in the **Appendix**, create the file and paste the
   exact contents shown.
4. Install dependencies and build docs to generate any derived files:
   ```bash
   pip install -e .
   cd docs && npm install && npm run build && cd ..
   ```
5. Commit the results:
   ```bash
   git add .
   git commit -m "Initial commit"
   ```

## Appendix
The following blocks contain the full text for every source file. Use the
surrounding comments to know where each block should be written.

### `.gitattributes`
```text
* text=auto
```

### `.gitignore`
```text
__pycache__/
*.py[cod]
.env
.venv/
venv/
outputs/*
!outputs/.gitkeep
docs/node_modules/
docs/.docusaurus/
docs/build/*
!docs/build/.gitkeep
```

### `.env.example`
```text
# Copy to .env and fill in your credentials
GITHUB_TOKEN=
# Optional embeddings configuration
# EMBED_MODEL=openai/text-embedding-3-small
# EMBED_DIMENSIONS=1536
# Formats produced by `scripts/convert.py` (comma-separated)
OUTPUT_FORMATS=markdown
# Set to 'true' to disable all GitHub Actions automation
DISABLE_ALL_WORKFLOWS=false
# Set individual workflows to 'true' to enable them
ENABLE_CONVERT_WORKFLOW=true
ENABLE_VALIDATE_WORKFLOW=true
ENABLE_VECTOR_WORKFLOW=true
ENABLE_PROMPT_ANALYSIS_WORKFLOW=true
ENABLE_PR_REVIEW_WORKFLOW=true
ENABLE_AUTO_MERGE_WORKFLOW=true
ENABLE_DOCS_WORKFLOW=true
```

### `pyproject.toml`
```text
[project]
name = "doc-ai-analysis-starter"
version = "0.1.0"
description = "Template repository for AI-powered document analysis."
requires-python = ">=3.10"
dependencies = [
    "docling",
    "openai",
    "pydantic",
    "pyyaml",
    "requests",
    "anyio",
    "python-dotenv",
]

[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["docai", "docai.*"]
```

### `docai/__init__.py`
```text
"""Reusable helpers for the doc-ai-analysis-starter template."""

from .metadata import DublinCoreDocument
from .converter import OutputFormat, convert_file, convert_files, suffix_for_format
from .github import run_prompt, review_pr, merge_pr, validate_file, build_vector_store

__all__ = [
    "DublinCoreDocument",
    "OutputFormat",
    "convert_file",
    "convert_files",
    "suffix_for_format",
    "validate_file",
    "build_vector_store",
    "run_prompt",
    "review_pr",
    "merge_pr",
]
```

### `docai/converter.py`
```text
<contents of docai/converter.py>
```

### `docai/github/__init__.py`
```text
from .prompts import run_prompt
from .pr import review_pr, merge_pr
from .validator import validate_file
from .vector import build_vector_store

__all__ = [
    "run_prompt",
    "review_pr",
    "merge_pr",
    "validate_file",
    "build_vector_store",
]
```

### `docai/github/pr.py`
```text
<contents of docai/github/pr.py>
```

### `docai/github/prompts.py`
```text
<contents of docai/github/prompts.py>
```

### `docai/github/validator.py`
```text
<contents of docai/github/validator.py>
```

### `docai/github/vector.py`
```text
<contents of docai/github/vector.py>
```

### `docai/metadata/__init__.py`
```text
"""Metadata utilities for docai."""

from .dublin_core import DublinCoreDocument

__all__ = ["DublinCoreDocument"]
```

### `docai/metadata/dublin_core.py`
```text
<contents of docai/metadata/dublin_core.py>
```

### Prompts (`prompts/*.prompt.yaml`)
```text
<contents of prompts/annual-report.prompt.yaml>
---
<contents of prompts/doc-analysis.prompt.yaml>
---
<contents of prompts/insider-trades.prompt.yaml>
---
<contents of prompts/pr-review.prompt.yaml>
---
<contents of prompts/sec-8k.prompt.yaml>
---
<contents of prompts/validate-output.prompt.yaml>
```

### Scripts (`scripts/*.py`)
```text
<contents of scripts/build_vector_store.py>
---
<contents of scripts/convert.py>
---
<contents of scripts/merge_pr.py>
---
<contents of scripts/review_pr.py>
---
<contents of scripts/run_prompt.py>
---
<contents of scripts/validate.py>
```

### Documentation (`docs/`)
```text
<contents of docs/docusaurus.config.js>
---
<contents of docs/package.json>
---
<contents of docs/docs/intro.md>
---
<contents of docs/sidebars.js>
---
<contents of docs/src/css/custom.css>
```

### GitHub Workflows (`.github/workflows/*.yaml`)
```text
<contents of .github/workflows/analyze.yaml>
---
<contents of .github/workflows/auto-merge.yaml>
---
<contents of .github/workflows/convert.yaml>
---
<contents of .github/workflows/docs.yaml>
---
<contents of .github/workflows/pr-review.yaml>
---
<contents of .github/workflows/validate.yaml>
---
<contents of .github/workflows/vector.yaml>
```

