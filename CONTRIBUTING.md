# Contributing

Thank you for contributing to this project.

## Release process
1. Update `CHANGELOG.md` with the new version section.
2. Bump the version in `pyproject.toml`.
3. Commit your changes.
4. Create and push a tag matching `vX.Y.Z`.
5. GitHub Actions will run tests, verify the changelog entry, build wheels and an sdist, upload the build artifacts, and publish the release to PyPI.

## Security checks

Run Bandit locally to catch common security issues before pushing changes:

```bash
python scripts/run_bandit.py
```

The script exits with a non-zero status when problems are found, mirroring the CI behaviour.
