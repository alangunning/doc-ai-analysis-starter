from pathlib import Path

import pytest
import typer

from doc_ai.cli.utils import EXTENSION_MAP, infer_format
from doc_ai.converter import OutputFormat


def test_doctags_extension_mapping_only_intended():
    """Ensure DOCTAGS output only maps from the .doctags extension."""
    doctag_extensions = [
        ext for ext, fmt in EXTENSION_MAP.items() if fmt == OutputFormat.DOCTAGS
    ]
    assert doctag_extensions == [".doctags"]


def test_infer_format_doctags_and_rejects_dogtags():
    """infer_format accepts .doctags and rejects .dogtags."""
    assert infer_format(Path("file.doctags")) == OutputFormat.DOCTAGS
    with pytest.raises(typer.BadParameter):
        infer_format(Path("file.dogtags"))
