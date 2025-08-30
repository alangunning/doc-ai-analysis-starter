# doc-ai-analysis-starter

A minimal template for automating document conversion, verification, prompt execution, and AI-assisted pull request review using GitHub Actions and GitHub Models. The repository also provides optional utilities for working with Dublin Core metadata.

## Requirements

- Python >= 3.10
- An `OPENAI_API_KEY` environment variable for scripts and workflows that call the OpenAI API.

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

### `dublin_core.py`

Utilities for creating and parsing Dublin Core metadata documents:

```python
from scripts.dublin_core import DublinCoreDocument
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
