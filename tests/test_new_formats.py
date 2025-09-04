from pathlib import Path

from doc_ai.cli.utils import infer_format, EXTENSION_MAP
from doc_ai.converter import OutputFormat, suffix_for_format


def test_new_output_formats():
    assert infer_format(Path('data.csv')) == OutputFormat.CSV
    assert infer_format(Path('report.summary.txt')) == OutputFormat.SUMMARY_TXT
    assert suffix_for_format(OutputFormat.CSV) == '.csv'
    assert suffix_for_format(OutputFormat.SUMMARY_TXT) == '.summary.txt'
    assert EXTENSION_MAP['.csv'] is OutputFormat.CSV
    assert EXTENSION_MAP['.summary.txt'] is OutputFormat.SUMMARY_TXT
