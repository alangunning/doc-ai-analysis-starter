---
title: GitHub Module
sidebar_position: 4
---

# GitHub Module

The `doc_ai.github` package provides helpers for working with GitHub and GitHub Models.

## Key APIs

### `run_prompt(prompt_file, input_text, model=None, base_url=None)`
Execute a prompt definition against input text and return the model output.

### `review_pr(pr_body, prompt_path, model=None, base_url=None)`
Run a pull request review prompt against the PR body text.

### `merge_pr(pr_number)`
Merge a pull request using the GitHub CLI.

### `validate_file(raw_path, rendered_path, fmt, prompt_path, model=None, base_url=None)`
Validate a rendered file against its source document and return the model's JSON verdict.

### `build_vector_store(src_dir)`
Generate vector embeddings for Markdown files in a directory and write `.embedding.json` files alongside each source.
