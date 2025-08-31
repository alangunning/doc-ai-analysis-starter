# ai-doc-analysis-starter

A starter template for converting documents, validating outputs, running prompts, and reviewing pull requests with AI. GitHub Actions orchestrate the steps and optional Dublin Core metadata lets workflows skip work they've already completed. The docs are published to https://alangunning.github.io/doc-ai-analysis-starter/docs/.

## Quick Start

1. **Requirements**
   - Python ≥ 3.10
   - `GITHUB_TOKEN` for access to GitHub Models and the GitHub CLI (you can [prototype for free](https://docs.github.com/en/github-models/use-github-models/prototyping-with-ai-models)).

2. **Install dependencies**
   ```bash
   pip install -e .
   cd docs
   npm install
   npm run build   # builds the optional Docusaurus docs
   ```

3. **Configuration**
   Copy `.env.example` to `.env` and edit values as needed. Environment variables provided by the runtime override values in the file. Set `DISABLE_ALL_WORKFLOWS=true` to skip automation or toggle individual workflows with `ENABLE_*` variables.

## Directory Layout

```
data/
  sec-8k/
    sec-8k.prompt.yaml
    apple-sec-8-k.pdf
    apple-sec-8-k.pdf.converted.md
    apple-sec-8-k.pdf.converted.html
    apple-sec-8-k.pdf.converted.json
    apple-sec-8-k.pdf.converted.text
    apple-sec-8-k.pdf.converted.doctags
    apple-sec-8-k.pdf.metadata.json
  annual-report/
    annual-report.prompt.yaml
    acme-2023.pdf
    acme-2023.pdf.converted.md
    acme-2023.pdf.converted.html
    acme-2023.pdf.converted.json
    acme-2023.pdf.converted.text
    acme-2023.pdf.converted.doctags
    acme-2023.pdf.metadata.json
```

## GitHub Workflows

- **Convert** – convert new documents under `data/**` and commit sibling outputs.
- **Validate** – compare converted files to sources and correct mismatches.
- **Vector** – generate embeddings for Markdown files on `main`.
- **Analysis** – run `<doc-type>.prompt.yaml` against Markdown documents and upload JSON.
- **PR Review** – review pull requests with an AI prompt; comment `/review` to rerun.
- **Docs** – build the Docusaurus site.
- **Auto Merge** – merge pull requests when a `/merge` comment is present (disabled by default).
- **Lint** – run Ruff for Python style.

### Dublin Core metadata

Each source file may have a `<name>.metadata.json` record storing a checksum and which steps have run. Workflows skip work when the metadata indicates a step is complete.

```mermaid
flowchart LR
    Commit[Commit document.pdf] --> Convert[Convert]
    Convert --> Validate[Validate]
    Validate --> Analysis[Run analysis]
    Analysis --> Vector[Vector]
    Vector --> Done[Done]
    Meta[(.metadata.json)] --> Convert
    Meta --> Validate
    Meta --> Analysis
    Meta --> Vector
    Convert --> Meta
    Validate --> Meta
    Analysis --> Meta
    Vector --> Meta
```

```mermaid
flowchart TD
    A[Commit or PR] --> B[Convert]
    B --> C[Validate]
    A --> D[Analysis]
    A --> E[PR Review]
    A --> F[Lint]
    Main[Push to main] --> G[Vector]
    Main --> H[Docs]
    Comment[/"/merge" comment/] --> I[Auto Merge]
    B --> M[(.metadata.json)]
    C --> M
    D --> M
    G --> M
```

For CLI usage and adding prompts, see the [scripts and prompts guide](https://alangunning.github.io/doc-ai-analysis-starter/docs/scripts-and-prompts).

## License

MIT
