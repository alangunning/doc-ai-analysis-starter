# AGENTS.md

## Recommended Actions for Initial Pre-release

- **Validate environment variables, tighten exception handling, and improve logging**
  - Warn when `EMBED_DIMENSIONS` or other variables are invalid.
  - Replace overly broad `except Exception` blocks with specific errors or log the exception details.
  - Log failures when closing existing logging handlers during reconfiguration.
- **Add automated accessibility and documentation checks**
  - Integrate an accessibility audit (e.g., axe-core or Lighthouse) into the documentation build.
  - Ensure all images in `docs/` include descriptive alt text.
- **Run full test suite, build docs, and verify CLI commands**
  - Execute `pre-commit run --all-files` and `pytest -q`.
  - Smoke-test primary CLI subcommands (`convert`, `validate`, `analyze`, `pipeline`, etc.) for runtime errors.
  - Build the documentation site (`npm run build`) and confirm pages load without missing assets or errors.
- **Finalize version metadata and tag the release**
  - Update `pyproject.toml` and `CHANGELOG.md` with the pre-release version.
  - Tag the repository and verify `doc-ai --version` reports the tagged version.

