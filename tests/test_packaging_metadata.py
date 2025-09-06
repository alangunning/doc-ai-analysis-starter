from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


def test_project_metadata_and_changelog():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    classifiers = set(project["classifiers"])
    assert "Programming Language :: Python :: 3.10" in classifiers
    assert "Programming Language :: Python :: 3.11" in classifiers
    assert "Programming Language :: Python :: 3.12" in classifiers
    assert "Typing :: Typed" in classifiers
    assert project["readme"]["content-type"] == "text/markdown"
    assert "doc-ai" in project["entry-points"]["console_scripts"]
    urls = project["urls"]
    assert "Changelog" in urls and urls["Changelog"].endswith("CHANGELOG.md")

    scm = data["tool"]["setuptools_scm"]
    assert scm.get("version_scheme") == "post-release"
    assert scm.get("local_scheme") == "no-local-version"

    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog.startswith("# Changelog")
    assert "[Unreleased]" in changelog
