---
sidebar_position: 3
---

# Directory structure

Documents are organized by type under `data/<doc-type>/`. Each directory contains a prompt definition named `<doc-type>.prompt.yaml` plus any number of source files (PDFs, Word docs, slide decks, etc.). Conversions, prompts, embeddings, and other derived files are written next to each source so every representation stays grouped together. Derived outputs retain the original extension and append `.converted.<ext>` (for example `.pdf.converted.md` or `.pdf.converted.html`) so raw sources can coexist with generated files:

```
data/
  sec-8k/
    sec-8k.prompt.yaml
    apple-sec-8-k.pdf
    apple-sec-8-k.pdf.converted.md
    apple-sec-8-k.pdf.converted.html
    apple-sec-8-k.sec-8k.json
  annual-report/
    annual-report.prompt.yaml
    acme-2023.pdf
    acme-2023.pdf.converted.md
    acme-2023.pdf.converted.html
    acme-2023.annual-report.json
```
