---
title: PDF vs Markdown Validation
sidebar_position: 7
---

# PDF vs Markdown Validation

Doc AI Starter validates Docling's Markdown output against the original PDF using OpenAI's file inputs. The Responses API currently accepts PDF (and image) attachments, so the Markdown is supplied as plain text. GitHub Models do not expose file uploads, so this step always targets OpenAI's API while the rest of the pipeline can continue using GitHub Models for text‑only prompts and embeddings.

The validator runs **Stage B** adjudication only, relying on the model to flag mismatches. To keep results reproducible, each call follows a strict "cite‑then‑claim" rubric and returns structured JSON with evidence for every discrepancy.

## Prompt discovery

`validate.py` and the accompanying workflow look for `.validate.prompt.yaml` files
to supply model instructions:

1. `<name>.validate.prompt.yaml` next to the source applies to that document only.
2. `validate.prompt.yaml` in the same directory covers an entire document type.

When neither file exists, the generic
`.github/prompts/validate-output.validate.prompt.yaml` is used. Pass `--prompt`
to the CLI to override this discovery.

## Validation with OpenAI (PDF + Markdown)

The snippet below uploads the PDF once and references it by `file_id` using
helpers from `doc_ai.openai`. The model compares the PDF with the provided
Markdown and returns a JSON verdict. Uploads default to the `user_data`
purpose; set `OPENAI_FILE_PURPOSE` to change it or `OPENAI_USE_UPLOAD=1` to
always use the resumable `/v1/uploads` API.

```python
from pathlib import Path
from openai import OpenAI
from doc_ai.openai import create_response, upload_file

OPENAI_BASE = "https://api.openai.com/v1"

def validate_pdf_vs_md_openai(pdf_path, md_path, model="gpt-4o-mini"):
    client = OpenAI(base_url=OPENAI_BASE)
    md = Path(md_path).read_text(encoding="utf-8")

    pdf_id = upload_file(client, pdf_path)

    resp = create_response(
        client,
        model=model,
        file_ids=[pdf_id],
        texts=[(
            'Compare the PDF to the Markdown. '
            'Return ONLY JSON: {"match": bool, "issues":[{"page": int, "pdf_quote": str, '
            '"md_quote": str, "type": str, "confidence": float}]}.'
            "\n\n### Markdown (truncated):\n" + md[:120_000]
        )],
        temperature=0,
    )
    return resp.output_text
```

For quick experiments you can inline the PDF as base64 instead of uploading it:

```python
from pathlib import Path
from openai import OpenAI
from doc_ai.openai import create_response

OPENAI_BASE = "https://api.openai.com/v1"

def validate_pdf_vs_md_openai_inline(pdf_path, md_path, model="gpt-4o-mini"):
    client = OpenAI(base_url=OPENAI_BASE)
    md = Path(md_path).read_text(encoding="utf-8")
    data = Path(pdf_path).read_bytes()

    resp = create_response(
        client,
        model=model,
        file_bytes=[(Path(pdf_path).name, data)],
        texts=[(
            "Compare with the Markdown and return ONLY the JSON schema above.\n\n"
            + md[:120_000]
        )],
        temperature=0,
    )
    return resp.output_text
```

## Later pipeline steps (Markdown only)

After validation, downstream scripts like analysis prompts or vector embeddings operate purely on Markdown. These steps can remain on GitHub Models by setting `BASE_MODEL_URL=https://models.github.ai/inference` and using model IDs such as `openai/gpt-4o` or `openai/text-embedding-3-large`.

## Practical limits & batching

Each request should stay below the platform limits (roughly ≤100 pages and ≤32 MB). For oversized documents, split the PDF into page batches and merge the results:

```python
match = all(batch.match for batch in batches)
issues = sum((batch.issues for batch in batches), [])
```

This pattern keeps every request within model limits while scaling to very large files.

### Guardrails for reliable adjudication

- Upload PDFs via `/v1/files` or, for multi‑gigabyte sources, the resumable `/v1/uploads` API.
- Pass the Markdown rendering as plain text rather than a file attachment.
- Keep every batch within ~100 pages and 32 MB; use page‑range chunks when necessary.
- Ask the model to emit only JSON with `match` and an `issues` array of objects containing `page`, `pdf_quote`, `md_quote`, `type` (`number_mismatch`, `missing_text`, `extra_text`, `table_structure`, `heading_level`, or `other`), and `confidence` (0‑1).
- Require the model to cite short snippets from both the PDF and Markdown for each issue to discourage hallucinations.

These guardrails make Stage B validation self‑contained while remaining auditable and reproducible.
