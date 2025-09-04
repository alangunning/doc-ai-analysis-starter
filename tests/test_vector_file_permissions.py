from types import SimpleNamespace

from doc_ai.github import vector


def test_vector_output_file_permissions(tmp_path, monkeypatch):
    md = tmp_path / "doc.md"
    md.write_text("content")
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    mock_client = SimpleNamespace(
        embeddings=SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(
                data=[SimpleNamespace(embedding=[0.1])]
            )
        )
    )
    monkeypatch.setattr("doc_ai.github.vector.OpenAI", lambda api_key, base_url: mock_client)
    vector.build_vector_store(tmp_path)
    out_file = md.with_suffix(".embedding.json")
    assert oct(out_file.stat().st_mode & 0o777) == "0o600"

