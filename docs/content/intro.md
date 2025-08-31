---
sidebar_position: 1
---

# Introduction

Doc AI Starter helps you explore document-processing workflows powered by GitHub's AI models. The template includes:

- a Python package with helpers for conversion, validation, and analysis
- CLI scripts that wrap the package functions
- GitHub Actions that automate each step of the pipeline, including AI-based PR review and optional auto-approve & merge
- this Docusaurus site with additional guides and references

## Pipeline at a Glance

1. Convert documents (`scripts/convert.py`, Convert workflow)
2. Validate conversions (`scripts/validate.py`, Validate workflow)
3. Run analysis prompts (`scripts/run_analysis.py`, Analysis workflow)
4. Build vector embeddings (`scripts/build_vector_store.py`, Vector workflow)

Each step writes to a `<name>.metadata.json` file so completed work can be skipped in subsequent runs.

## Getting Started

1. Follow the Quick Start steps in the repository `README.md` to install dependencies.
2. Inspect the sample documents under `data/` or add your own files.
3. Use the CLI scripts to convert, validate, and analyze documents.
4. Review the workflow docs to see how GitHub Actions connect the pieces.

Use the navigation to dive into specific topics:

- [Workflow Overview](./workflows)
- [CLI Scripts and Prompts](./scripts-and-prompts)
- [Converter Module](./converter)
- [GitHub Module](./github)
- [Metadata Module](./metadata)
