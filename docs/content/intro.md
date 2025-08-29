---
sidebar_position: 1
slug: /
---

# Introduction

Doc AI Starter is a showcase template for developers exploring GitHub's AI models. It illustrates how to structure `.prompt.yaml` files and apply the models to advanced document analysis. The pipeline demonstrates how to convert documents, validate outputs, run analysis prompts, and review pull requests—all inside the GitHub ecosystem.

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
2. Inspect the sample documents under `data/` or add your own files.
3. Use the CLI scripts to convert, validate, and analyze documents.
4. Review the workflow docs to see how GitHub Actions connect the pieces.

Use the navigation to dive into specific topics:

- [Workflow Overview](./workflows)
- [CLI Scripts and Prompts](./scripts-and-prompts)
- [Converter Module](./converter)
- [GitHub Module](./github)
- [Metadata Module](./metadata)
