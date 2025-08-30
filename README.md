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

## Scripts

### `convert_to_markdown.py`

Convert raw documents (e.g., PDFs) into Markdown:

```bash
python scripts/convert_to_markdown.py data/raw --outdir data/markdown
```

### `validate_markdown.py`

Validate that a Markdown file matches the original document:

```bash
python scripts/validate_markdown.py data/raw/example.pdf data/markdown/example.md
```

### `run_prompt.py`

Run a prompt definition against a Markdown document and save JSON output:

```bash
python scripts/run_prompt.py prompts/annual-report.prompt.yaml data/markdown/example.md --outdir outputs/annual-report
```

### `build_vector_store.py`

Generate embeddings for Markdown documents and store them under `vector_store/`:

```bash
python scripts/build_vector_store.py data/markdown vector_store
```

Embeddings are fetched from the GitHub Models API using `openai/text-embedding-3-small` by
default. The script sends a POST request to `https://models.github.ai/inference/embeddings`
with your `GITHUB_TOKEN` and writes the returned float vectors to JSON files.

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

- **Convert** – auto-converts files in `data/raw/` to Markdown and commits results.
- **Validate** – checks converted Markdown against the source document and auto-corrects mismatches.
- **Vector** – builds a vector store from Markdown documents after validation.
- **Prompt Analysis** – executes prompt templates against Markdown documents and uploads JSON output as artifacts.
- **PR Review** – summarizes pull requests.
- **Auto Merge** – merges pull requests when a `/merge` comment is posted.

## Adding Prompts

To add a new prompt:

1. Create a `.prompt.yaml` file in `prompts/` using the GitHub Models structure (`name`, `description`, `model`, `modelParameters`, `messages`).
2. Optionally update the `prompt-analysis.yml` matrix to include the new prompt name if you want it to run automatically in the workflow.
No changes to the Python scripts are required.

## License

MIT
