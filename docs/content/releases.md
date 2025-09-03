---
title: Releases
---

The `doc-ai-analysis-starter` project follows
[semantic versioning](https://semver.org/). When you're ready to publish a new
version:

1. Bump `__version__` in `doc_ai/__init__.py` and update `CHANGELOG.md` with the
   summary of changes.
2. Commit the changes and tag the release with a `vMAJOR.MINOR.PATCH` tag.
3. Push the tag to GitHub.

The `CI` workflow automatically runs `ruff`, `pytest`, builds the source and
wheel distributions, and publishes the artifacts to PyPI for tagged releases.
