---
sidebar_position: 0
slug: /
---

# Introduction

Doc AI is a showcase template for developers exploring GitHub's AI models. It illustrates how to structure `.prompt.yaml` files and apply the models to advanced document analysis. The pipeline demonstrates how to convert documents, validate outputs, run analysis prompts, and review pull requests—all inside the GitHub ecosystem.

> **Note:** Sample files are stored directly in the repository to keep the example self-contained. For production use or large datasets, move documents to Git LFS or an external object store.

The template includes:

- a Python package with helpers for conversion, validation, and analysis
- CLI scripts that wrap the package functions
- GitHub Actions that automate each step of the pipeline, including AI-based PR review and optional auto-approve & merge
- sample `.prompt.yaml` files that define prompts for GitHub's AI models
- this Docusaurus site with additional guides and references

Commit a document to `data/` and the workflows automatically convert, validate, analyze, and embed it—demonstrating the end-to-end automation.

## Pipeline at a Glance

1. Convert documents (`scripts/convert.py`, Convert workflow)
2. Validate conversions (`scripts/validate.py`, Validate workflow)
3. Run analysis prompts (`scripts/run_analysis.py`, Analysis workflow)
4. Build vector embeddings (`scripts/build_vector_store.py`, Vector workflow)

Each step writes to a `<name>.metadata.json` file so completed work can be skipped in subsequent runs.

## Getting Started

1. Follow the Quick Start steps in the repository `README.md` to install dependencies.
2. Install the pre-commit hooks and run `pre-commit run --all-files` before committing changes.
3. Inspect the sample documents under `data/` or add your own files.
4. Use the CLI scripts to convert, validate, and analyze documents.
5. Review the workflow docs to see how GitHub Actions connect the pieces.

Use the navigation to dive into specific topics:

- [Workflow Overview](guides/workflows)
- [CLI Scripts and Prompts](guides/scripts-and-prompts)
- [Converter Module](doc_ai/converter)
- [GitHub Module](doc_ai/github)
- [Metadata Module](doc_ai/metadata)
