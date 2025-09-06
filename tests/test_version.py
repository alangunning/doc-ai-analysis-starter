import importlib.metadata as metadata

import doc_ai


def test_version_matches_metadata():
    assert doc_ai.__version__ == metadata.version("doc-ai")
