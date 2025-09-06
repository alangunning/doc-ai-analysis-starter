"""Reusable helpers for the Doc AI Analysis Starter template."""

try:
    from ._version import version as __version__
except ImportError:  # pragma: no cover
    __version__ = "0.0.0"

from .converter import OutputFormat, convert_file, convert_files, suffix_for_format
from .github import build_vector_store, merge_pr, review_pr, run_prompt, validate_file
from .metadata import DublinCoreDocument

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
