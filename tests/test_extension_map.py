from doc_ai.cli.utils import EXTENSION_MAP
from doc_ai.converter import OutputFormat


def test_doctags_mapping_unique() -> None:
    """Ensure DOCTAGS mapping appears only once and uses .doctags."""
    entries = [ext for ext, fmt in EXTENSION_MAP.items() if fmt == OutputFormat.DOCTAGS]
    assert entries == [".doctags"]


def test_no_dogtags_entry() -> None:
    """The obsolete .dogtags extension should not be accepted."""
    assert ".dogtags" not in EXTENSION_MAP
