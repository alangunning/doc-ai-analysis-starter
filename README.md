# airnub-ai-template

A minimal template for automating document conversion, verification, prompt execution, and AI-assisted pull request review using GitHub Actions and GitHub Models.

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
python scripts/convert_to_markdown.py documents/raw --outdir documents
```

### `verify_markdown.py`

Validate that a Markdown file matches the original document:

```bash
python scripts/verify_markdown.py path/to/original.pdf path/to/document.md
```

### `run_prompt.py`

Run a prompt definition against a Markdown document and save JSON output:

```bash
python scripts/run_prompt.py prompts/annual-report.prompt.yaml documents/example.md --outdir outputs/annual-report
```

## GitHub Workflows

- **Convert to Markdown** – auto-converts files in `documents/raw/` to Markdown and commits results.
- **Verify Markdown** – checks converted Markdown against the source document and auto-corrects mismatches.
- **Prompt Analysis** – executes prompt templates against Markdown documents and uploads JSON output as artifacts.
- **AI PR Review** – summarizes pull requests and supports `/merge` commands via comments for auto-merging.

## Adding Prompts

To add a new prompt:

1. Create a `.prompt.yaml` file in `prompts/` following the existing format.
2. Optionally update the `prompt-analysis.yml` matrix to include the new prompt name if you want it to run automatically in the workflow.
No changes to the Python scripts are required.

## License

MIT
