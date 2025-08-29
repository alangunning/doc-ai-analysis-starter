# ai-doc-analysis-starter

A minimal template for automating document conversion, verification, prompt execution, and AI-assisted pull request review using GitHub Actions and GitHub Models. The repository also provides optional utilities for working with Dublin Core metadata.

## Requirements

- Python >= 3.10
- Environment variables such as `GITHUB_TOKEN` for model access and GitHub CLI operations (see `.env.example`).

Create a `.env` file based on `.env.example` and supply your token (and optional settings). Environment variables provided by the runtime (for example via GitHub Secrets) override values in the file, allowing cloud agents to inject `GITHUB_TOKEN` automatically. Each workflow's model can be overridden by setting `PR_REVIEW_MODEL`, `VALIDATE_MODEL`, `ANALYZE_MODEL`, or `EMBED_MODEL`.

Set `DISABLE_ALL_WORKFLOWS=true` in the `.env` file to skip every GitHub Action without editing workflow files. Individual workflows remain disabled unless explicitly enabled with variables like `ENABLE_CONVERT_WORKFLOW`, `ENABLE_VALIDATE_WORKFLOW`, `ENABLE_VECTOR_WORKFLOW`, `ENABLE_PROMPT_ANALYSIS_WORKFLOW`, `ENABLE_PR_REVIEW_WORKFLOW`, `ENABLE_DOCS_WORKFLOW`, `ENABLE_AUTO_MERGE_WORKFLOW`, or `ENABLE_LINT_WORKFLOW`.

Install dependencies with:

```bash
pip install -e .
```

For the Docusaurus docs site:

```bash
cd docs
npm install
npm run build
```

## Directory layout

Documents are organized by type under `data/<doc-type>/`. Each directory
contains a prompt definition named `<doc-type>.prompt.yaml` plus any number of
source files (PDFs, Word docs, slide decks, etc.). Conversions, prompts,
embeddings, and other derived files are written next to each source so every
representation stays grouped together. Derived outputs retain the original
extension and append `.converted.<ext>` (for example `.pdf.converted.md` or
`.pdf.converted.html`) so raw sources can coexist with generated files:

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

## Scripts

Each CLI tool is a thin wrapper around reusable functions in the
`ai_doc_analysis_starter` package. GitHub-specific helpers live under
`ai_doc_analysis_starter.github` so the same interfaces can be extended to other
providers later.

### `convert.py`

Convert raw documents (PDFs, Word docs, slide decks, etc.) into one or more
formats:

```bash
python scripts/convert.py data/sample/sample.pdf --format markdown --format html
```

Outputs are written alongside the source file, so the example above produces
`data/sample/sample.pdf.converted.md` and `data/sample/sample.pdf.converted.html`. Pass `--format` multiple
times to emit additional outputs (`json`, `text`, or `doctags`). Alternatively,
set a comma-separated list in the `OUTPUT_FORMATS` environment variable so the
script and the convert workflow default to those formats (e.g.,
`OUTPUT_FORMATS=markdown,html`). The underlying library is wrapped by
`ai_doc_analysis_starter.converter` so you can swap engines without changing calling code.

### `validate.py`

Validate that a converted file (Markdown, HTML, JSON, etc.) matches the original document:

```bash
python scripts/validate.py data/example/example.pdf data/example/example.pdf.converted.md
```
Override the model with `--model` or `VALIDATE_MODEL`.

### `run_analysis.py`

Run a prompt definition stored in a document-type directory against a Markdown
document and save JSON output next to the source file:

```bash
python scripts/run_analysis.py data/sec-8k/sec-8k.prompt.yaml data/sec-8k/apple-sec-8-k.pdf.converted.md
```

The above writes `data/sec-8k/apple-sec-8-k.sec-8k.json`. Override the model
with `--model` or `ANALYZE_MODEL`.

### `build_vector_store.py`

Generate embeddings for Markdown documents and write them next to each source file:

```bash
python scripts/build_vector_store.py data
```

Embeddings are fetched from the GitHub Models API using
`openai/text-embedding-3-small` by default. Override the model with
`EMBED_MODEL`. The script sends a POST request to
`https://models.github.ai/inference/embeddings` with your `GITHUB_TOKEN` and
writes the returned float vectors to `<name>.embedding.json` files in the same
directory as each Markdown document.

### `review_pr.py`

Produce AI-assisted PR feedback using a prompt file:

```bash
python scripts/review_pr.py prompts/pr-review.prompt.yaml "PR body text"
```
Override the model with `--model` or `PR_REVIEW_MODEL`.

### `merge_pr.py`

Merge a pull request when authorized:

```bash
python scripts/merge_pr.py 123
```

### Dublin Core utilities

Reusable helpers for creating and parsing Dublin Core metadata documents:

```python
from ai_doc_analysis_starter.metadata import DublinCoreDocument
```

Each source file may include a sibling ``*.dc.json`` metadata record. The
metadata stores a blake2b checksum and tracks which processing steps have been
completed. A typical metadata file looks like:

```json
{
  "blake2b": "<file hash>",
  "extra": {
    "steps": {
      "conversion": true,
      "validation": true,
      "analysis": true,
      "vector": true
    }
  }
}
```

On each run the scripts compute the current checksum. If it matches the value
in the metadata and the relevant step is marked complete, that step is skipped.
Otherwise the step runs and the metadata file is updated so subsequent runs only
process changed or incomplete documents.

```mermaid
flowchart LR
    Commit[Commit document.pdf] --> Convert[Convert]
    Convert --> Validate[Validate]
    Validate --> Analysis[Run analysis]
    Analysis --> Vector[Vector]
    Vector --> Done[Done]
    Meta[(.dc.json)] --> Convert
    Meta --> Validate
    Meta --> Analysis
    Meta --> Vector
    Convert --> Meta
    Validate --> Meta
    Analysis --> Meta
    Vector --> Meta
```

## GitHub Workflows

- **Convert** – auto-converts newly added documents under `data/**` and commits
  sibling format outputs, skipping files when `.dc.json` indicates conversion is
  complete. Its commit triggers the Validate workflow.
- **Validate** – checks converted outputs against the source documents and
  auto-corrects mismatches, skipping unchanged files via metadata.
- **Vector** – generates embeddings for Markdown files on `main` and writes
  them next to the sources, omitting documents whose metadata already records
  the `vector` step.
- **Analysis** – auto-discovers `<doc-type>.prompt.yaml` files in each
  `data/<doc-type>` directory, runs them against every Markdown document in
  that directory, and uploads JSON output as artifacts, re-running only when
  prompts haven't been marked complete.
- **PR Review** – runs an AI model against each pull request and posts the
  result as a comment, ending with `/merge` when the changes are approved.
  Comment `/review` on a pull request to trigger the workflow manually.
- **Docs** – builds the Docusaurus site and deploys to GitHub Pages.
- **Auto Merge** – approves and merges pull requests when a `/merge` comment is
  posted. Disabled by default; enable by setting `ENABLE_AUTO_MERGE_WORKFLOW=true`
  in `.env`.
- **Lint** – runs Ruff to check Python code style.

The PR review prompt asks the model to append `/merge` when no further changes
are required. Posting this comment triggers the Auto Merge workflow, which
approves and merges the pull request. Use `/review` in a comment to re-run the
PR Review workflow on demand.

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
    B --> M[(.dc.json)]
    C --> M
    D --> M
    G --> M
```

## Adding Prompts

To add a new prompt:

1. Create a `.prompt.yaml` file next to the document (e.g.,
   `data/acme-report/acme-report.prompt.yaml`).
2. Commit the prompt and document; the Analysis workflow will run it automatically.
No changes to the Python scripts are required.

## License

MIT
