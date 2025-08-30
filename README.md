# doc-ai-analysis-starter

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

### `validate_markdown.py`

Validate that a Markdown file matches the original document:

```bash
python scripts/validate_markdown.py path/to/original.pdf path/to/document.md
```

### `run_prompt.py`

Run a prompt definition against a Markdown document and save JSON output:

```bash
python scripts/run_prompt.py prompts/annual-report.prompt.yaml documents/example.md --outdir outputs/annual-report
```

## GitHub Workflows

- **Convert** – auto-converts files in `documents/raw/` to Markdown and commits results.
- **Validate** – checks converted Markdown against the source document and auto-corrects mismatches.
- **Prompt Analysis** – executes prompt templates against Markdown documents and uploads JSON output as artifacts.
- **Build Vector Store** – embeds validated Markdown documents into a vector store.
- **PR Review** – summarizes pull requests.
- **Review Comment** – posts an AI review when someone comments `/review` on a pull request.
- **Auto Merge** – merges pull requests when a `/merge` comment is posted.

## How to Showcase

1. Push a PDF into `documents/raw/`.
2. The Convert workflow produces a Markdown file in `documents/`.
3. The Validate workflow checks the Markdown and auto-corrects mismatches.
4. The Prompt Analysis workflow runs `run_prompt.py` for each prompt and uploads results.
5. The Build Vector Store workflow updates `vector_store/embeddings.json`.
6. Open a pull request to see the PR summary; comment `/review` for an AI review and `/merge` to merge automatically.

## Adding Prompts

To add a new prompt:

1. Create a `.prompt.yaml` file in `prompts/` following the existing format.
2. Optionally update the `prompt-analysis.yml` matrix to include the new prompt name if you want it to run automatically in the workflow.
No changes to the Python scripts are required.

## License

MIT
