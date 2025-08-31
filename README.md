
# AI Doc Analysis Starter

AI Doc Analysis Starter is a template for building end‑to‑end document pipelines with GitHub's AI models. It shows how to convert files, validate the output, run custom analysis prompts, generate embeddings, and review pull requests. Full documentation lives in the `docs/` folder and is published at [https://alangunning.github.io/doc-ai-analysis-starter/docs/](https://alangunning.github.io/doc-ai-analysis-starter/docs/).

## Quick Start

1. **Requirements**
   - Python ≥ 3.10
   - Node ≥ 18 for building the docs (optional)
   - `GITHUB_TOKEN` for access to GitHub Models and the GitHub CLI (you can [prototype for free](https://docs.github.com/en/github-models/use-github-models/prototyping-with-ai-models))

2. **Install**

   ```bash
   pip install -e .
   ```

   Optionally build the documentation site:

   ```bash
   cd docs
   npm install
   npm run build
   cd ..
   ```

3. **Configure**

   Copy `.env.example` to `.env` and adjust variables as needed. Environment variables from the runtime override values in the file. Set `DISABLE_ALL_WORKFLOWS=true` to skip automation or toggle individual workflows with `ENABLE_*` variables.

   #### Workflow Toggles

   | Variable | Workflow |
   | --- | --- |
   | `ENABLE_CONVERT_WORKFLOW` | Convert documents |
   | `ENABLE_VALIDATE_WORKFLOW` | Validate outputs |
   | `ENABLE_PROMPT_ANALYSIS_WORKFLOW` | Run analysis prompts |
   | `ENABLE_VECTOR_WORKFLOW` | Generate vector embeddings |
   | `ENABLE_PR_REVIEW_WORKFLOW` | Review pull requests |
   | `ENABLE_DOCS_WORKFLOW` | Build documentation site |
   | `ENABLE_AUTO_MERGE_WORKFLOW` | Auto merge pull requests |
   | `ENABLE_LINT_WORKFLOW` | Run lint checks |

   Example `.env` snippet:

   ```env
   # run convert and PR review workflows
   ENABLE_CONVERT_WORKFLOW=true
   ENABLE_PR_REVIEW_WORKFLOW=true

   # skip validation and docs workflows
   ENABLE_VALIDATE_WORKFLOW=false
   ENABLE_DOCS_WORKFLOW=false
   ```

4. **Try it out**

Convert a document and validate the Markdown output:

```bash
python scripts/convert.py data/sec-form-8k/apple-sec-8-k.pdf --format markdown
python scripts/validate.py data/sec-form-8k/apple-sec-8-k.pdf data/sec-form-8k/apple-sec-8-k.pdf.converted.md
```

Or run the whole pipeline in one go with the orchestrator CLI:

```bash
ai-doc-analysis pipeline data/sec-form-8k/
```

## Directory Overview

```
ai_doc_analysis_starter/   # Python package
scripts/                   # CLI helpers
prompts/                   # Prompt definitions
data/                      # Sample documents and outputs
docs/                      # Docusaurus documentation
```

`data` is organized by document type. Each source file has converted siblings and an optional `<name>.metadata.json` file that records which steps have completed.

Example structure:

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

## Documentation

Guides for each part of the template live in the `docs/` folder and are published at [https://alangunning.github.io/doc-ai-analysis-starter/docs/](https://alangunning.github.io/doc-ai-analysis-starter/docs/). Useful starting points:

- [Introduction](https://alangunning.github.io/doc-ai-analysis-starter/docs/content/intro) – project overview and navigation
- [Workflow Overview](https://alangunning.github.io/doc-ai-analysis-starter/docs/content/workflows) – how the GitHub Actions fit together
- [CLI Scripts and Prompts](https://alangunning.github.io/doc-ai-analysis-starter/docs/content/scripts-and-prompts) – run conversions and analyses locally
- [Converter Module](https://alangunning.github.io/doc-ai-analysis-starter/docs/content/converter) – programmatic file conversion
- [GitHub Module](https://alangunning.github.io/doc-ai-analysis-starter/docs/content/github) – helpers for GitHub Models
- [Metadata Module](https://alangunning.github.io/doc-ai-analysis-starter/docs/content/metadata) – track processing state

## Automated Workflows

GitHub Actions automate the common pipeline steps:

- **Convert** – convert new documents under `data/**` using Docling and commit sibling outputs.
- **Validate** – use the GitHub AI model to compare converted files to sources and correct mismatches.
- **Analysis** – run `<doc-type>.prompt.yaml` against Markdown documents with the GitHub AI model and upload JSON.
- **Vector** – generate embeddings for Markdown files on `main` with the GitHub AI model.
- **PR Review** – review pull requests with the GitHub AI model; comment `/review` to rerun.
- **Docs** – build the Docusaurus site.
- **Auto Merge** – after an AI review, a `/merge` comment triggers the workflow to auto‑approve and merge the pull request with the GitHub AI model (disabled by default).
- **Lint** – run Ruff for Python style.

Each run updates the companion metadata so completed steps are skipped. See the [metadata docs](https://alangunning.github.io/doc-ai-analysis-starter/docs/metadata) for a full overview of the schema and available fields. Configure which steps run using the environment variables in the [Workflow Toggles](#workflow-toggles) table.

```mermaid
graph LR;
    Commit[Commit document.pdf] --> Convert[Convert Documents (Docling)];
    Convert --> Validate[Validate Outputs (GitHub AI model)];
    Validate --> Analysis[Run Analysis Prompts (GitHub AI model)];
    Analysis --> Vector[Generate Vector Embeddings (GitHub AI model)];
    Vector --> Done[Workflow Complete];
    Meta[(Metadata Record (.metadata.json))] --> Convert;
    Meta --> Validate;
    Meta --> Analysis;
    Meta --> Vector;
    Convert --> Meta;
    Validate --> Meta;
    Analysis --> Meta;
    Vector --> Meta;
```

```mermaid
graph TD;
    A[Commit or PR] --> B[Convert Documents (Docling)];
    B --> C[Validate Outputs (GitHub AI model)];
    A --> D[Run Analysis Prompts (GitHub AI model)];
    A --> E[Review PR with AI (GitHub AI model)];
    A --> F[Run Lint Checks];
    Main[Push to main] --> G[Generate Vector Embeddings (GitHub AI model)];
    Main --> H[Build Documentation];
    Comment["/merge"] --> I[Auto Merge PR];
    B --> M[(Metadata Record (.metadata.json))];
    C --> M;
    D --> M;
    G --> M;
```

For CLI usage and adding prompts, see `docs/content/scripts-and-prompts.md`.

## License

MIT
