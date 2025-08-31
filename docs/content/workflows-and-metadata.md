---
title: Workflows & Metadata
sidebar_position: 3
---

# Workflows & Metadata

GitHub Actions coordinate the document processing pipeline. Each stage writes to
or reads from a `<name>.metadata.json` sidecar so repeated runs can skip
completed work.

## Workflow overview

```mermaid
flowchart LR
    A[Commit document.pdf] --> B[Convert]
    B --> C[Validate]
    C --> D[Run analysis]
    D --> E[Vector]
    E --> F[Done]
    B --> M[(metadata)]
    C --> M
    D --> M
    E --> M
    M --> B
    M --> C
    M --> D
    M --> E
```

The sidecar captures checksums and which stages have finished.

## Pull request and main branch

```mermaid
flowchart TD
    PR[Pull Request] --> Convert
    PR --> Validate
    PR --> Analyze[Analysis]
    PR --> Lint
    Convert --> Meta[(metadata)]
    Validate --> Meta
    Analyze --> Meta
    Main[Push to main] --> Vector
    Main --> Docs[Build docs]
    Vector --> Meta
```

Pull requests run the full pipeline except docs and embeddings, which run only
on the default branch.

## Metadata fields

`<name>.metadata.json` resembles:

```json
{
  "checksum": "...",
  "convert": true,
  "validate": false,
  "analysis": true,
  "vector": false
}
```

- **checksum** – hash of the source file
- **convert/validate/analysis/vector** – flags marking completed steps

Workflows check this file to determine whether to operate on a given document.
