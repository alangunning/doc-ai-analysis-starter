# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.1.0b3] - 2025-09-06

## [0.1.0b2] - 2025-09-06

## [0.1.0-alpha.0] - 2025-09-06

### Added
- Use `setuptools-scm` for automatic versioning.
- Release instructions for tagging and verifying the CLI version with `doc-ai --version`.
- Script to generate validation and analysis prompts from a PDF in one run.
- Documentation for PDF input cost considerations and new script usage.
- Launch `doc-ai` without arguments to enter an interactive shell with a built-in `cd` command.
- REPL commands for listing and duplicating document types and topics.
- External editor support, improved help, shell escapes, and better batch error handling in the REPL.
- Support for platform-wide global configuration files.
- `--log-level` and `--log-file` options for fine-grained logging control.
- Automated release workflow for testing, building, and publishing tagged releases to PyPI.
- Initial release of `doc-ai` with proper package metadata and version export.
