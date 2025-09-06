# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- Script to generate validation and analysis prompts from a PDF in one run.
- Documentation for PDF input cost considerations and new script usage.
- Launch `doc-ai` without arguments to enter an interactive shell with a built-in `cd` command.
- Support for platform-wide global configuration files.
- `--log-level` and `--log-file` options for fine-grained logging control.
### Changed
- Shell escapes are now disabled by default. Set `DOC_AI_ALLOW_SHELL=true` to enable
  them, which emits a startup warning in the REPL.

## [0.1.0] - 2025-09-03
### Added
- Initial release of `doc-ai-analysis-starter` with proper package metadata and
  version export.
