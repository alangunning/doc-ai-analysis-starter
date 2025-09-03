---
title: Releases
---

This project follows [semantic versioning](https://semver.org/).  When you're
ready to publish a new version:

1. Update `CHANGELOG.md` with the new version number and summary of changes.
2. Commit the changelog and tag the release with a `vMAJOR.MINOR.PATCH` tag.
3. Push the tag to GitHub.

The `CI` workflow automatically runs `ruff`, `pytest`, builds the source and
wheel distributions, and publishes the artifacts to PyPI for tagged releases.
