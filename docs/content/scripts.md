---
title: CLI Scripts & Prompts
sidebar_position: 2
---

# CLI Scripts

The `scripts` directory houses small command-line utilities that orchestrate
document processing and prompt execution. Each script accepts `--help` for full
usage details; the examples below show common tasks.

## convert.py

Turn a source document into one or more derived formats. Outputs are written
next to the source file.

```bash
python scripts/convert.py data/sec-8k/apple-sec-8-k.pdf --format markdown --format html
```

- Supported formats: `markdown`, `html`, `json`, `text`, `doctags`
- Can also set `OUTPUT_FORMATS=markdown,html,...` in the environment.

## validate.py

Compare a converted file with the original document to ensure the conversion
looks correct.

```bash
python scripts/validate.py data/sec-8k/apple-sec-8-k.pdf data/sec-8k/apple-sec-8-k.pdf.converted.md
```

- Override the model with `--model` or `VALIDATE_MODEL`.

## run_analysis.py

Execute a prompt definition against a Markdown file and store JSON output.

```bash
python scripts/run_analysis.py data/sec-8k/sec-8k.prompt.yaml data/sec-8k/apple-sec-8-k.pdf.converted.md
```

- Result: `data/sec-8k/apple-sec-8-k.sec-8k.json`
- Model override: `--model` or `ANALYZE_MODEL`.

## build_vector_store.py

Generate embeddings for Markdown files and write them alongside each source.

```bash
python scripts/build_vector_store.py data
```

- Use `EMBED_MODEL` and optionally `EMBED_DIMENSIONS` to customize embeddings.

## review_pr.py

Provide AI-assisted feedback for a pull request by supplying a prompt file and
the pull request body.

```bash
python scripts/review_pr.py prompts/pr-review.prompt.yaml "PR body text"
```

- Model override: `--model` or `PR_REVIEW_MODEL`.

## merge_pr.py

Merge a pull request when authorized.

```bash
python scripts/merge_pr.py 123
```

# Adding Prompts

1. Create a `.prompt.yaml` file next to the document (e.g.,
   `data/sec-8k/sec-8k.prompt.yaml`).
2. Commit the prompt and document. The Analysis workflow will run the prompt and
   write `<document>.<prompt>.json`.
3. Update `.metadata.json` sidecars as needed to record completion.
