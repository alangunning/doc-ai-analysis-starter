---
title: GitHub Module
sidebar_position: 4
---

# GitHub Module

The `doc_ai.github` package provides helpers for working with GitHub and GitHub Models.

## Authentication and Permissions

GitHub Models require a token with the `Models:read` scope. When creating a fine-grained personal access token, choose **Read** access under **Account permissions → Models**. This setting is separate from repository permissions; without it, requests return `PermissionDeniedError: Error code 403` with `no_access` to the model.

## Key APIs

### `run_prompt(prompt_file, input_text, model=None, base_url=None)`
Execute a prompt definition against input text and return the model output.

### `review_pr(pr_body, prompt_path, model=None, base_url=None)`
Run a pull request review prompt against the PR body text.

### `merge_pr(pr_number)`
Merge a pull request using the GitHub CLI.

### `validate_file(raw_path, rendered_path, fmt, prompt_path, model=None, base_url=None, show_progress=False)`
Validate a rendered file against its source document and return the model's JSON verdict. Pass
`show_progress=True` to emit upload progress callbacks for integration with the CLI's progress bars.

Uploaded files use `purpose="user_data"` as recommended by OpenAI's file API guidelines.

The helper delegates to `doc_ai.openai.create_response`, uploading any local
paths (switching to the resumable `/v1/uploads` service for large files) and
passing remote URLs directly to the Responses API. GitHub Models do not support
file uploads, so the function automatically falls back to OpenAI's API at
`https://api.openai.com/v1` (using the `OPENAI_API_KEY` token) whenever the base
URL points to the GitHub provider or is left unset. This approach lets the model
compare long documents without running into context limits. For cost‑sensitive
jobs, specify a smaller model such as `gpt-4o-mini` or chunk the source document
into smaller pieces and validate them individually.

### `build_vector_store(src_dir)`
Generate vector embeddings for Markdown files in a directory and write `.embedding.json` files alongside each source.
