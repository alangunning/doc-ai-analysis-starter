
# Doc AI Analysis Starter

Doc AI Analysis Starter is a template for building end‑to‑end document pipelines with GitHub's AI models. It shows how to convert files, validate the output, run custom analysis prompts, generate embeddings, and review pull requests. Full documentation lives in the `docs/` folder and is published at [https://alangunning.github.io/doc-ai-analysis-starter/docs/](https://alangunning.github.io/doc-ai-analysis-starter/docs/).

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
doc_ai/                     # Python package
scripts/                  # CLI helpers
.github/workflows/        # CI workflows
.github/prompts/          # Prompt definitions
data/                     # Sample documents and outputs
docs/                     # Docusaurus documentation
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
    apple-sec-form-10q.pdf
    apple-sec-form-10q.pdf.converted.md
    apple-sec-form-10q.pdf.converted.html
    apple-sec-form-10q.pdf.converted.json
    apple-sec-form-10q.pdf.converted.text
    apple-sec-form-10q.pdf.converted.doctags
    apple-sec-form-10q.pdf.metadata.json
  sec-form-4/
    sec-form-4.prompt.yaml
    apple-sec-form-4.pdf
    apple-sec-form-4.pdf.converted.md
    apple-sec-form-4.pdf.converted.html
    apple-sec-form-4.pdf.converted.json
    apple-sec-form-4.pdf.converted.text
    apple-sec-form-4.pdf.converted.doctags
    apple-sec-form-4.pdf.metadata.json
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

GitHub Actions tie the pieces together. Each workflow runs on a specific trigger and can be disabled with its `ENABLE_*` variable.

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| Convert | Push to `data/**` | Convert new documents with Docling and commit sibling outputs |
| Validate | Push converted outputs | Compare rendered files to sources and correct mismatches |
| Analysis | Push Markdown or `.prompt.yaml`, or manual dispatch | Run custom prompts against Markdown and upload JSON |
| Vector | Push to `main` with Markdown | Generate embeddings for search |
| PR Review | Pull request or `/review` comment | Provide AI feedback on the PR body |
| Docs | Push to `docs/**` on `main` | Build and publish the documentation site |
| Auto Merge | `/merge` issue comment | Approve and merge a pull request after review |
| Lint | Push/PR touching Python files | Run Ruff style checks |

Each run updates the companion metadata so completed steps are skipped. See the [metadata docs](https://alangunning.github.io/doc-ai-analysis-starter/docs/content/metadata) for a full overview of the schema and available fields. Configure which steps run using the environment variables in the [Workflow Toggles](#workflow-toggles) table.

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
