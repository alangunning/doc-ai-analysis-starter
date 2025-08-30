# doc-ai-analysis-starter

A minimal template for automating document conversion, verification, prompt execution, and AI-assisted pull request review using GitHub Actions and GitHub Models. The repository also provides optional utilities for working with Dublin Core metadata.

## Requirements

- Python >= 3.10
- Environment variables such as `GITHUB_TOKEN` for model access and GitHub CLI operations (see `.env.example`).

Create a `.env` file based on `.env.example` and supply your token (and optional settings). Environment variables provided by the runtime (for example via GitHub Secrets) override values in the file, allowing cloud agents to inject `GITHUB_TOKEN` automatically.

Set `DISABLE_ALL_WORKFLOWS=true` in the `.env` file to skip every GitHub Action without editing workflow files. Individual workflows remain disabled unless explicitly enabled with variables like `ENABLE_CONVERT_WORKFLOW`, `ENABLE_VALIDATE_WORKFLOW`, `ENABLE_VECTOR_WORKFLOW`, `ENABLE_PROMPT_ANALYSIS_WORKFLOW`, `ENABLE_PR_REVIEW_WORKFLOW`, or `ENABLE_AUTO_MERGE_WORKFLOW`.

Install dependencies with:

```bash
pip install -e .
```

## Directory layout

Each source document is stored under `data/<name>/<name>.pdf`. Conversions,
embeddings, and other derived files are written alongside the source so every
representation stays grouped together:

```
data/
  sample/
    sample.pdf
    sample.md
    sample.html
    sample.embedding.json
```

## Scripts

Each CLI tool is a thin wrapper around reusable functions in the `docai` package.
GitHub-specific helpers live under `docai.github` so the same interfaces can be
extended to other providers later.

### `convert.py`

Convert raw documents (e.g., PDFs) into one or more formats:

```bash
python scripts/convert.py data/sample/sample.pdf --format markdown --format html
```

Outputs are written alongside the source file, so the example above produces
`data/sample/sample.md` and `data/sample/sample.html`. Pass `--format` multiple
times to emit additional outputs (`json`, `text`, or `doctags`). Alternatively,
set a comma-separated list in the `OUTPUT_FORMATS` environment variable so the
script and the convert workflow default to those formats (e.g.,
`OUTPUT_FORMATS=markdown,html`). The underlying library is wrapped by
`docai.converter` so you can swap engines without changing calling code.

### `validate.py`

Validate that a converted file (Markdown, HTML, JSON, etc.) matches the original document:

```bash
python scripts/validate.py data/example/example.pdf data/example/example.md
```

### `run_prompt.py`

Run a prompt definition against a Markdown document and save JSON output:

```bash
python scripts/run_prompt.py prompts/annual-report.prompt.yaml data/example/example.md --outdir outputs/annual-report
```

### `build_vector_store.py`

Generate embeddings for Markdown documents and write them next to each source file:

```bash
python scripts/build_vector_store.py data
```

Embeddings are fetched from the GitHub Models API using
`openai/text-embedding-3-small` by default. The script sends a POST request to
`https://models.github.ai/inference/embeddings` with your `GITHUB_TOKEN` and
writes the returned float vectors to `<name>.embedding.json` files in the same
directory as each Markdown document.

### `review_pr.py`

Produce AI-assisted PR feedback using a prompt file:

```bash
python scripts/review_pr.py prompts/pr-review.prompt.yaml "PR body text"
```

### `merge_pr.py`

Merge a pull request when authorized:

```bash
python scripts/merge_pr.py 123
```

### Dublin Core utilities

Reusable helpers for creating and parsing Dublin Core metadata documents:

```python
from docai.dublin_core import DublinCoreDocument
```

## GitHub Workflows

- **Convert** – auto-converts newly added `data/**/*.pdf` files and commits sibling format outputs.
- **Validate** – checks converted outputs against the source documents and auto-corrects mismatches.
- **Vector** – generates embeddings for Markdown files on `main` and writes them next to the sources.
- **Analyze** – executes prompt templates against Markdown documents and uploads JSON output as artifacts.
- **PR Review** – summarizes pull requests.
- **Auto Merge** – merges pull requests when a `/merge` comment is posted.

## Adding Prompts

To add a new prompt:

1. Create a `.prompt.yaml` file in `prompts/` using the GitHub Models structure (`name`, `description`, `model`, `modelParameters`, `messages`).
2. Optionally update the `analyze.yaml` matrix to include the new prompt name if you want it to run automatically in the workflow.
No changes to the Python scripts are required.

## License

MIT
