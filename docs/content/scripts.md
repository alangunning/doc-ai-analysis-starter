---
sidebar_position: 4
---

# CLI scripts

Each CLI tool is a thin wrapper around reusable functions in the `ai_doc_analysis_starter` package. GitHub-specific helpers live under `ai_doc_analysis_starter.github` so the same interfaces can be extended to other providers later.

## `convert.py`

Convert raw documents (PDFs, Word docs, slide decks, etc.) into one or more formats:

```bash
python scripts/convert.py data/sample/sample.pdf --format markdown --format html
```

Outputs are written alongside the source file, so the example above produces `data/sample/sample.pdf.converted.md` and `data/sample/sample.pdf.converted.html`. Pass `--format` multiple times to emit additional outputs (`json`, `text`, or `doctags`). Alternatively, set a comma-separated list in the `OUTPUT_FORMATS` environment variable so the script and the convert workflow default to those formats (e.g., `OUTPUT_FORMATS=markdown,html`). The underlying library is wrapped by `ai_doc_analysis_starter.converter` so you can swap engines without changing calling code.

## `validate.py`

Validate that a converted file (Markdown, HTML, JSON, etc.) matches the original document:

```bash
python scripts/validate.py data/example/example.pdf data/example/example.pdf.converted.md
```

Override the model with `--model` or `VALIDATE_MODEL`.

## `run_analysis.py`

Run a prompt definition stored in a document-type directory against a Markdown document and save JSON output next to the source file:

```bash
python scripts/run_analysis.py data/sec-8k/sec-8k.prompt.yaml data/sec-8k/apple-sec-8-k.pdf.converted.md
```

The above writes `data/sec-8k/apple-sec-8-k.sec-8k.json`. Override the model with `--model` or `ANALYZE_MODEL`.

## `build_vector_store.py`

Generate embeddings for Markdown documents and write them next to each source file:

```bash
python scripts/build_vector_store.py data
```

Embeddings are fetched from the GitHub Models API using `openai/text-embedding-3-small` by default. Override the model with `EMBED_MODEL`. The script sends a POST request to `https://models.github.ai/inference/embeddings` with your `GITHUB_TOKEN` and writes the returned float vectors to `<name>.embedding.json` files in the same directory as each Markdown document.

## `review_pr.py`

Produce AI-assisted PR feedback using a prompt file:

```bash
python scripts/review_pr.py prompts/pr-review.prompt.yaml "PR body text"
```

Override the model with `--model` or `PR_REVIEW_MODEL`.

## `merge_pr.py`

Merge a pull request when authorized:

```bash
python scripts/merge_pr.py 123
```

## Dublin Core utilities

Reusable helpers for creating and parsing Dublin Core metadata documents:

```python
from ai_doc_analysis_starter.metadata import DublinCoreDocument
```

Each source file may include a sibling `*.dc.json` metadata record. The metadata stores a blake2b checksum and tracks which processing steps have been completed. A typical metadata file looks like:

```json
{
  "blake2b": "<file hash>",
  "extra": {
    "steps": {
      "conversion": true,
      "validation": true,
      "analysis": true,
      "vector": true
    }
  }
}
```

On each run the scripts compute the current checksum. If it matches the value in the metadata and the relevant step is marked complete, that step is skipped. Otherwise the step runs and the metadata file is updated so subsequent runs only process changed or incomplete documents.
