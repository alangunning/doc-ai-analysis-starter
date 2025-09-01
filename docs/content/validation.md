---
title: PDF vs Markdown Validation
sidebar_position: 7
---

# PDF vs Markdown Validation

Doc AI Starter validates Docling's Markdown output against the original PDF using OpenAI's file inputs. GitHub Models do not expose file uploads, so this step always targets OpenAI's API while the rest of the pipeline can continue using GitHub Models for text‑only prompts and embeddings.

## Validation with OpenAI (PDF + Markdown)

The snippet below uploads the PDF once and references it by `file_id` using
helpers from `doc_ai.openai`. The model compares the PDF with the provided
Markdown and returns a JSON verdict.

```python
from pathlib import Path
from openai import OpenAI
from doc_ai.openai import create_response, upload_file

OPENAI_BASE = "https://api.openai.com/v1"

def validate_pdf_vs_md_openai(pdf_path, md_path, model="gpt-4o-mini"):
    client = OpenAI(base_url=OPENAI_BASE)
    md = Path(md_path).read_text(encoding="utf-8")

    pdf_id = upload_file(client, pdf_path, purpose="user_data")

    resp = create_response(
        client,
        model=model,
        file_ids=[pdf_id],
        texts=[(
            'Compare the PDF to the Markdown. '
            'Return ONLY JSON: {"match": bool, "issues":[{"where": str, "type": str, "detail": str}]}.'
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
