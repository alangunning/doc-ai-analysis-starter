"""Reusable helpers for the Doc AI Starter template."""

from .metadata import DublinCoreDocument
from .converter import OutputFormat, convert_file, convert_files, suffix_for_format
from .github import run_prompt, review_pr, merge_pr, validate_file, build_vector_store

try:  # pragma: no cover - handled by packaging
    from ._version import version as __version__
except Exception:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = [
    "DublinCoreDocument",
    "OutputFormat",
    "convert_file",
    "convert_files",
    "suffix_for_format",
    "validate_file",
    "build_vector_store",
    "run_prompt",
    "review_pr",
    "merge_pr",
    "__version__",
]
