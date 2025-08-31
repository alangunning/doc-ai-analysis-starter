# AI Doc Analysis Starter

A minimal template for converting, validating, analyzing, and reviewing documents with GitHub Actions and GitHub Models.

## Quick start

1. **Requirements**
   - Python >= 3.10
   - `GITHUB_TOKEN` and other environment variables (see [`.env.example`](./.env.example))
2. **Setup**
   ```bash
   cp .env.example .env  # add your token
   pip install -e .
   ```
3. **Docs site (optional)**
   ```bash
   cd docs
   npm install
   npm run build
   ```

See the `docs` directory for full setup, CLI usage, and workflow details.

## Document workflow

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

## GitHub automation

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

## License

MIT
