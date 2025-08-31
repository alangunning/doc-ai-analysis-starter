---
title: Workflow Overview
sidebar_position: 2
---

# Workflow Overview

The template's GitHub Actions coordinate the document pipeline from raw uploads to analysis results. Documents live under `data/`, grouped by form type, and each source file keeps converted siblings and metadata records. A typical layout looks like:

```
data/
  sec-form-8k/
    sec-form-8k.prompt.yaml
    apple-sec-8-k.pdf
    apple-sec-8-k.pdf.converted.md
    apple-sec-8-k.pdf.converted.html
    apple-sec-8-k.pdf.converted.json
    apple-sec-8-k.pdf.converted.text
    apple-sec-8-k.pdf.converted.doctags
    apple-sec-8-k.pdf.metadata.json
  sec-form-10q/
    sec-form-10q.prompt.yaml
    acme-2024-q1.pdf
    acme-2024-q1.pdf.converted.md
    acme-2024-q1.pdf.converted.html
    acme-2024-q1.pdf.converted.json
    acme-2024-q1.pdf.converted.text
    acme-2024-q1.pdf.converted.doctags
    acme-2024-q1.pdf.metadata.json
  sec-form-4/
    sec-form-4.prompt.yaml
    insider-2024-01-01.pdf
    insider-2024-01-01.pdf.converted.md
    insider-2024-01-01.pdf.converted.html
    insider-2024-01-01.pdf.converted.json
    insider-2024-01-01.pdf.converted.text
    insider-2024-01-01.pdf.converted.doctags
    insider-2024-01-01.pdf.metadata.json
```

Each workflow can run independently, but together they form an end-to-end process:

- **Convert** – convert new documents under `data/**` using Docling and commit sibling outputs.
- **Validate** – use the GitHub AI model to compare converted files to sources and correct mismatches.
- **Analysis** – run `<doc-type>.prompt.yaml` against Markdown documents with the GitHub AI model and upload JSON.
- **Vector** – generate embeddings for Markdown files on `main` with the GitHub AI model.
- **PR Review** – review pull requests with the GitHub AI model; comment `/review` to rerun.
- **Docs** – build the Docusaurus site.
- **Auto Merge** – merge pull requests when a `/merge` comment is present (disabled by default).
- **Lint** – run Ruff for Python style.

Each step updates the document's `<name>.metadata.json` record so completed work is skipped on subsequent runs.

```mermaid
flowchart LR
    Commit[Commit document.pdf] --> Convert[Convert Documents (Docling)]
    Convert --> Validate[Validate Outputs (GitHub AI model)]
    Validate --> Analysis[Run Analysis Prompts (GitHub AI model)]
    Analysis --> Vector[Generate Vector Embeddings (GitHub AI model)]
    Vector --> Done[Workflow Complete]
    Meta[(Metadata Record (.metadata.json))] --> Convert
    Meta --> Validate
    Meta --> Analysis
    Meta --> Vector
    Convert --> Meta
    Validate --> Meta
    Analysis --> Meta
    Vector --> Meta
```
