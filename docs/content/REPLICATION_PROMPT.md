---
sidebar_position: 2
---

# AI Agent Prompt: Recreate `ai-doc-analysis-starter`

You are an AI coding agent with access to a Bash shell and GitHub CLI. Rebuild
this repository **without cloning or downloading any remote template**.
All file contents required to recreate the project are included below.
Follow the steps exactly and stop on any error.

## Steps
1. Create and initialize a new repository:
   ```bash
   mkdir NEW_REPO
   cd NEW_REPO
   git init -b main
   ```
2. Reproduce the directory tree:
   ```bash
   mkdir -p data outputs prompts scripts ai_doc_analysis_starter/converter ai_doc_analysis_starter/github ai_doc_analysis_starter/metadata docs/content docs/src/css .github/workflows docs/build
   touch data/.gitkeep outputs/.gitkeep docs/build/.gitkeep
   ```
3. For each file path listed in the **Appendix**, create the file and paste the
   exact contents shown.
4. Install dependencies and build docs to generate any derived files:
   ```bash
   pip install -e .
   cd docs && npm install && npm run build && cd ..
   ```
5. Commit the results:
   ```bash
   git add .
   git commit -m "Initial commit"
   ```

## Appendix
The following blocks contain the full text for every source file.

### `.gitattributes`
```text
* text=auto
```

### `.gitignore`
```text
__pycache__/
*.py[cod]
.env
.venv/
venv/
outputs/*
!outputs/.gitkeep
docs/node_modules/
docs/.docusaurus/
docs/build/*
!docs/build/.gitkeep
```

### `.env.example`
```text
# Copy to .env and fill in your credentials
GITHUB_TOKEN=
# Optional model overrides
# PR_REVIEW_MODEL=gpt-4.1
# VALIDATE_MODEL=gpt-4.1
# ANALYZE_MODEL=gpt-4.1
# EMBED_MODEL=openai/text-embedding-3-small
# EMBED_DIMENSIONS=1536
# Formats produced by `scripts/convert.py` (comma-separated)
OUTPUT_FORMATS=markdown
# Set to 'true' to disable all GitHub Actions automation
DISABLE_ALL_WORKFLOWS=false
# Set individual workflows to 'true' to enable them
ENABLE_CONVERT_WORKFLOW=true
ENABLE_VALIDATE_WORKFLOW=true
ENABLE_VECTOR_WORKFLOW=true
ENABLE_PROMPT_ANALYSIS_WORKFLOW=true
ENABLE_PR_REVIEW_WORKFLOW=true
ENABLE_AUTO_MERGE_WORKFLOW=true
ENABLE_DOCS_WORKFLOW=true
```

### `pyproject.toml`
```text
[project]
name = "ai-doc-analysis-starter"
version = "0.1.0"
description = "Template repository for AI-powered document analysis."
requires-python = ">=3.10"
dependencies = [
    "docling",
    "openai",
    "pydantic",
    "pyyaml",
    "requests",
    "anyio",
    "python-dotenv",
]

[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["ai_doc_analysis_starter", "ai_doc_analysis_starter.*"]
```

### `ai_doc_analysis_starter/__init__.py`
```text
"""Reusable helpers for the ai-doc-analysis-starter template."""

from .metadata import DublinCoreDocument
from .converter import OutputFormat, convert_file, convert_files, suffix_for_format
from .github import run_prompt, review_pr, merge_pr, validate_file, build_vector_store

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
]
```

### `ai_doc_analysis_starter/converter/__init__.py`
```text
from .document_converter import OutputFormat, convert_file, convert_files, suffix_for_format

__all__ = [
    "OutputFormat",
    "convert_file",
    "convert_files",
    "suffix_for_format",
]
```

### `ai_doc_analysis_starter/converter/document_converter.py`
```text
"""Unified document conversion helpers.

Provides a thin wrapper around the current conversion backend (Docling)
so callers can request various output formats without depending on the
underlying library.  The interface is intentionally small to allow
future backends to be swapped in without touching calling code.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Dict, Union

from docling.document_converter import DocumentConverter as _DoclingConverter

# Supported high level output formats.
class OutputFormat(str, Enum):
    """Canonical output formats supported by the converter."""

    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    TEXT = "text"
    DOCTAGS = "doctags"


# Map output formats to the method on the Docling Document object
# that renders that representation.
_METHOD_MAP: Dict[OutputFormat, str] = {
    OutputFormat.MARKDOWN: "as_markdown",
    OutputFormat.HTML: "as_html",
    OutputFormat.JSON: "as_json",
    OutputFormat.TEXT: "as_text",
    OutputFormat.DOCTAGS: "as_doctags",
}

# File extension for each format so callers can write outputs with a
# predictable suffix.
_SUFFIX_MAP: Dict[OutputFormat, str] = {
    OutputFormat.MARKDOWN: ".md",
    OutputFormat.HTML: ".html",
    OutputFormat.JSON: ".json",
    OutputFormat.TEXT: ".txt",
    OutputFormat.DOCTAGS: ".doctags",
}


def convert_files(
    input_path: Path, outputs: Dict[OutputFormat, Path]
) -> Dict[OutputFormat, Path]:
    """Convert ``input_path`` to multiple formats.

    ``outputs`` maps each desired ``OutputFormat`` to the file path where the
    rendered content should be written.  The source document is converted only
    once, and the requested representations are emitted to their respective
    destinations.  The mapping of formats to the paths that were written is
    returned for convenience.
    """

    converter = _DoclingConverter()
    document = converter.convert(input_path)

    written: Dict[OutputFormat, Path] = {}
    for fmt, out_path in outputs.items():
        out_path.parent.mkdir(parents=True, exist_ok=True)
        render_method = getattr(document, _METHOD_MAP[fmt])
        content: Union[str, bytes] = render_method()
        if isinstance(content, bytes):
            out_path.write_bytes(content)
        else:
            out_path.write_text(content, encoding="utf-8")
        written[fmt] = out_path

    return written


def convert_file(input_path: Path, output_path: Path, fmt: OutputFormat) -> Path:
    """Convert ``input_path`` to a single ``fmt`` and return the written path."""

    return convert_files(input_path, {fmt: output_path})[fmt]


def suffix_for_format(fmt: OutputFormat) -> str:
    """Return the default file suffix for ``fmt``."""

    return _SUFFIX_MAP[fmt]


__all__ = ["OutputFormat", "convert_files", "convert_file", "suffix_for_format"]
```

### `ai_doc_analysis_starter/github/__init__.py`
```text
from .prompts import run_prompt
from .pr import review_pr, merge_pr
from .validator import validate_file
from .vector import build_vector_store

__all__ = [
    "run_prompt",
    "review_pr",
    "merge_pr",
    "validate_file",
    "build_vector_store",
]
```

### `ai_doc_analysis_starter/github/pr.py`
```text
"""Pull request helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .prompts import run_prompt


def review_pr(pr_body: str, prompt_path: Path) -> str:
    """Run the PR review prompt against ``pr_body``."""

    return run_prompt(prompt_path, pr_body)


def merge_pr(pr_number: int) -> None:
    """Merge pull request ``pr_number`` using the GitHub CLI."""

    subprocess.run(["gh", "pr", "merge", str(pr_number), "--merge"], check=True)


__all__ = ["review_pr", "merge_pr"]
```

### `ai_doc_analysis_starter/github/prompts.py`
```text
"""Prompt execution helpers."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def run_prompt(prompt_file: Path, input_text: str) -> str:
    """Execute ``prompt_file`` against ``input_text`` and return model output."""

    spec = yaml.safe_load(prompt_file.read_text())
    messages = [dict(m) for m in spec["messages"]]
    for msg in reversed(messages):
        if msg.get("role") == "user":
            msg["content"] = msg.get("content", "") + "\n\n" + input_text
            break
    client = OpenAI(
        api_key=os.getenv("GITHUB_TOKEN"),
        base_url="https://models.github.ai",
    )
    response = client.responses.create(
        model=spec["model"],
        **spec.get("modelParameters", {}),
        input=messages,
    )
    return response.output[0].content[0].get("text", "")


__all__ = ["run_prompt"]
```

### `ai_doc_analysis_starter/github/validator.py`
```text
"""Rendering validation helpers."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Dict

import yaml
from dotenv import load_dotenv
from openai import OpenAI

from ..converter import OutputFormat

load_dotenv()


def _build_messages(raw_bytes: bytes, rendered_text: str, fmt: OutputFormat, prompt_path: Path) -> Dict:
    spec = yaml.safe_load(prompt_path.read_text())
    messages = [dict(m) for m in spec["messages"]]
    for i, msg in enumerate(messages):
        if msg.get("role") == "user":
            text = msg.get("content", "").format(format=fmt.value)
            messages[i]["content"] = [
                {"type": "input_text", "text": text},
                {"type": "document", "format": "pdf", "b64_content": base64.b64encode(raw_bytes).decode()},
                {"type": "text", "text": rendered_text},
            ]
            break
    return spec, messages


def validate_file(
    raw_path: Path,
    rendered_path: Path,
    fmt: OutputFormat,
    prompt_path: Path,
    model: str | None = None,
) -> Dict:
    """Validate ``rendered_path`` against ``raw_path`` for ``fmt``.

    Returns the model's JSON verdict as a dictionary.
    """

    spec, messages = _build_messages(
        raw_path.read_bytes(), rendered_path.read_text(), fmt, prompt_path
    )
    client = OpenAI(
        api_key=os.getenv("GITHUB_TOKEN"),
        base_url="https://models.github.ai",
    )
    result = client.responses.create(
        model=model or spec["model"],
        **spec.get("modelParameters", {}),
        input=messages,
    )
    text = result.output[0].content[0].get("text", "{}")
    return json.loads(text)


__all__ = ["validate_file"]
```

### `ai_doc_analysis_starter/github/vector.py`
```text
"""Embedding helpers for Markdown files."""

from __future__ import annotations

import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL = os.getenv("EMBED_MODEL", "openai/text-embedding-3-small")
EMBED_DIMENSIONS = os.getenv("EMBED_DIMENSIONS")


def build_vector_store(src_dir: Path) -> None:
    """Generate embeddings for Markdown files in ``src_dir``."""

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set")

    api_url = "https://models.github.ai/inference/embeddings"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    for md_file in src_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        payload: dict[str, object] = {
            "model": EMBED_MODEL,
            "input": [text],
            "encoding_format": "float",
        }
        if EMBED_DIMENSIONS:
            payload["dimensions"] = int(EMBED_DIMENSIONS)
        resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        embedding = resp.json()["data"][0]["embedding"]
        out_file = md_file.with_suffix(".embedding.json")
        out_file.write_text(
            json.dumps({"file": str(md_file), "embedding": embedding}) + "\n",
            encoding="utf-8",
        )


__all__ = ["build_vector_store"]
```

### `ai_doc_analysis_starter/metadata/__init__.py`
```text
"""Metadata utilities for ai_doc_analysis_starter."""

from .dublin_core import DublinCoreDocument

__all__ = ["DublinCoreDocument"]
```

### `ai_doc_analysis_starter/metadata/dublin_core.py`
```text
"""Dublin Core metadata utilities."""

from __future__ import annotations

import base64
import datetime
import json
import lzma
import pickle
import uuid
import zlib
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional, cast
from xml.etree import ElementTree

COMPRESSION_TYPE: Optional[Literal["zlib", "lzma"]] = "zlib"

# namespaces
XML_NAMESPACES = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
}

# Dublin Core Metadata Element to DCMI Element mapping
FIELD_TO_DC_ELEMENT = {
    "title": "dc:title",
    "description": "dc:description",
    "publisher": "dc:publisher",
    "creator": "dc:creator",
    "subject": "dc:subject",
    "contributor": "dc:contributor",
    "date": "dc:date",
    "type": "dc:type",
    "format": "dc:format",
    "identifier": "dc:identifier",
    "source": "dc:source",
    "language": "dc:language",
    "relation": "dc:relation",
    "coverage": "dc:coverage",
    "rights": "dc:rights",
    "audience": "dcterms:audience",
    "mediator": "dcterms:mediator",
    "accrual_method": "dcterms:accrualMethod",
    "accrual_periodicity": "dcterms:accrualPeriodicity",
    "accrual_policy": "dcterms:accrualPolicy",
    "alternative": "dcterms:alternative",
    "bibliographic_citation": "dcterms:bibliographicCitation",
    "conforms_to": "dcterms:conformsTo",
    "date_accepted": "dcterms:dateAccepted",
    "date_available": "dcterms:dateAvailable",
    "date_created": "dcterms:created",
    "date_issued": "dcterms:issued",
    "date_modified": "dcterms:modified",
    "date_submitted": "dcterms:dateSubmitted",
    "extent": "dcterms:extent",
    "has_format": "dcterms:hasFormat",
    "has_part": "dcterms:hasPart",
    "has_version": "dcterms:hasVersion",
    "is_format_of": "dcterms:isFormatOf",
    "is_part_of": "dcterms:isPartOf",
    "is_referenced_by": "dcterms:isReferencedBy",
    "is_replaced_by": "dcterms:isReplacedBy",
    "is_required_by": "dcterms:isRequiredBy",
    "issued": "dcterms:issued",
    "is_version_of": "dcterms:isVersionOf",
    "license": "dcterms:license",
    "provenance": "dcterms:provenance",
    "rights_holder": "dcterms:rightsHolder",
    "spatial": "dcterms:spatial",
    "temporal": "dcterms:temporal",
    "valid": "dcterms:valid",
}

DC_ELEMENT_TO_FIELD = {v: k for k, v in FIELD_TO_DC_ELEMENT.items()}


# pylint: disable=too-many-instance-attributes
@dataclass
class DublinCoreDocument:
    """Dublin Core Metadata Document class."""

    # Core DCMI terms
    title: Optional[str] = None
    description: Optional[str] = None
    publisher: Optional[str] = None
    creator: Optional[List[str]] = field(default_factory=list)
    subject: Optional[List[str]] = field(default_factory=list)
    contributor: Optional[List[str]] = field(default_factory=list)
    date: Optional[datetime.datetime] = None
    type: Optional[str] = None
    format: Optional[str] = None
    identifier: Optional[str] = None
    source: Optional[str] = None
    language: Optional[str] = None
    relation: Optional[str] = None
    coverage: Optional[str] = None
    rights: Optional[str] = None

    # Additional DCMI terms
    audience: Optional[str] = None
    mediator: Optional[str] = None
    accrual_method: Optional[str] = None
    accrual_periodicity: Optional[str] = None
    accrual_policy: Optional[str] = None
    alternative: Optional[str] = None
    bibliographic_citation: Optional[str] = None
    conforms_to: Optional[str] = None
    date_accepted: Optional[datetime.datetime] = None
    date_available: Optional[datetime.datetime] = None
    date_created: Optional[datetime.datetime] = None
    date_issued: Optional[datetime.datetime] = None
    date_modified: Optional[datetime.datetime] = None
    date_submitted: Optional[datetime.datetime] = None
    extent: Optional[str] = None
    has_format: Optional[str] = None
    has_part: Optional[str] = None
    has_version: Optional[str] = None
    is_format_of: Optional[str] = None
    is_part_of: Optional[str] = None
    is_referenced_by: Optional[str] = None
    is_replaced_by: Optional[str] = None
    is_required_by: Optional[str] = None
    issued: Optional[datetime.datetime] = None
    is_version_of: Optional[str] = None
    license: Optional[str] = None
    provenance: Optional[str] = None
    rights_holder: Optional[str] = None
    spatial: Optional[str] = None
    temporal: Optional[str] = None
    valid: Optional[datetime.datetime] = None

    # Non-DC fields to allow for storage of document contents or additional metadata
    content: Optional[bytes] = None
    blake2b: Optional[str] = None
    id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    size: int = 0
    extra: Optional[Dict[str, int | float | str | tuple | list | dict]] = field(
        default_factory=dict
    )

    def encode_content(self) -> Optional[str]:
        """Encode the content using the specified compression type."""
        if self.content:
            if COMPRESSION_TYPE == "zlib":
                return base64.b64encode(zlib.compress(self.content)).decode()
            if COMPRESSION_TYPE == "lzma":
                return base64.b64encode(lzma.compress(self.content)).decode()
            return base64.b64encode(self.content).decode()
        return None

    @classmethod
    def decode_content(cls, encoded_content: str) -> Optional[bytes]:
        """Decode the content using the specified compression type."""
        try:
            if COMPRESSION_TYPE == "zlib":
                return zlib.decompress(base64.b64decode(encoded_content))
            if COMPRESSION_TYPE == "lzma":
                return lzma.decompress(base64.b64decode(encoded_content))
            return base64.b64decode(encoded_content)
        except Exception:  # pylint: disable=broad-except
            return None

    def normalize_dates(self) -> bool:
        """Attempt to normalize all date fields to datetime objects."""
        status = True
        for field_name in [
            "date",
            "date_accepted",
            "date_available",
            "date_created",
            "date_issued",
            "date_modified",
            "date_submitted",
            "issued",
            "valid",
        ]:
            if hasattr(self, field_name) and getattr(self, field_name):
                try:
                    if isinstance(getattr(self, field_name), str):
                        setattr(
                            self,
                            field_name,
                            datetime.datetime.fromisoformat(getattr(self, field_name)),
                        )
                except ValueError:
                    status = False

        return status

    def to_dict(self) -> dict:
        """Convert the DublinCoreDocument to a dictionary."""
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> DublinCoreDocument:
        """Create a DublinCoreDocument from a dictionary."""
        document = DublinCoreDocument(**data)
        document.normalize_dates()
        return document

    def to_min_dict(self) -> Dict[str, Any]:
        """Serialize the Dublin Core document to a minimal dictionary."""
        return {
            field_name: value
            for field_name, value in self.to_dict().items()
            if value not in ([], {}, "", None)
        }

    def to_json(self) -> str:
        """Serialize the Dublin Core document to JSON."""
        self_dict = self.to_min_dict()
        if "content" in self_dict:
            self_dict["content"] = self.encode_content()
        return json.dumps(self_dict, default=self._default_serializer, indent=4)

    @staticmethod
    def from_json(json_data: str) -> DublinCoreDocument:
        """Load a DublinCoreDocument from JSON data."""
        data = json.loads(json_data)
        if "content" in data:
            data["content"] = DublinCoreDocument.decode_content(data["content"])
        document = DublinCoreDocument(**data)
        document.normalize_dates()
        return document

    def to_json_ld(self) -> str:
        """Serialize the Dublin Core document to JSON-LD."""
        json_ld_dict = {
            "@context": {"dc": "http://purl.org/dc/elements/1.1/"},
            **{
                FIELD_TO_DC_ELEMENT[field_name]: value
                for field_name, value in self.to_min_dict().items()
                if field_name in FIELD_TO_DC_ELEMENT and value is not None
            },
        }
        return json.dumps(json_ld_dict, default=self._default_serializer, indent=4)

    @staticmethod
    def from_json_ld(json_ld_data: str) -> DublinCoreDocument:
        """Load a DublinCoreDocument from JSON-LD data."""
        data = json.loads(json_ld_data)
        dc_data = {}
        for field_name, dc_element in FIELD_TO_DC_ELEMENT.items():
            if dc_element in data:
                dc_data[field_name] = data[dc_element]
        document = DublinCoreDocument(**dc_data)
        document.normalize_dates()
        return document

    def to_xml(self) -> str:
        """Serialize the Dublin Core document to XML."""
        root_element = ElementTree.Element("metadata")
        root_element.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")
        for field_name, value in self.to_min_dict().items():
            if field_name in FIELD_TO_DC_ELEMENT and value is not None:
                if isinstance(value, list):
                    for item in value:
                        element = ElementTree.SubElement(
                            root_element, FIELD_TO_DC_ELEMENT[field_name]
                        )
                        element.text = str(item)
                elif isinstance(value, (datetime.date, datetime.datetime)):
                    element = ElementTree.SubElement(root_element, FIELD_TO_DC_ELEMENT[field_name])
                    element.text = value.isoformat()
                else:
                    element = ElementTree.SubElement(root_element, FIELD_TO_DC_ELEMENT[field_name])
                    element.text = str(value)

        return ElementTree.tostring(root_element, encoding="unicode", method="xml")

    @staticmethod
    def from_xml(xml_data: str) -> DublinCoreDocument:
        """Load a DublinCoreDocument from XML data."""
        root = ElementTree.fromstring(xml_data)
        dc_data: Dict[str, Any] = {}
        for field_name, dc_element in FIELD_TO_DC_ELEMENT.items():
            elements = root.findall(f".//{dc_element}", XML_NAMESPACES)
            if elements:
                texts = [cast(str, elem.text) for elem in elements]
                if len(texts) > 1 and field_name in {"creator", "subject", "contributor"}:
                    dc_data[field_name] = texts
                else:
                    dc_data[field_name] = texts[0]
        document = DublinCoreDocument(**dc_data)
        document.normalize_dates()
        return document

    def to_rdf(self) -> str:
        """Serialize the Dublin Core document to RDF/XML."""
        rdf_root = ElementTree.Element(
            "rdf:RDF",
            {
                "xmlns:rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "xmlns:dc": "http://purl.org/dc/elements/1.1/",
                "xmlns:dcterms": "http://purl.org/dc/terms/",
            },
        )
        description = ElementTree.SubElement(rdf_root, "rdf:Description")
        for field_name, value in self.to_min_dict().items():
            if field_name in FIELD_TO_DC_ELEMENT and value is not None:
                if isinstance(value, list):
                    for item in value:
                        element = ElementTree.SubElement(
                            description, FIELD_TO_DC_ELEMENT[field_name]
                        )
                        element.text = str(item)
                elif isinstance(value, (datetime.date, datetime.datetime)):
                    element = ElementTree.SubElement(description, FIELD_TO_DC_ELEMENT[field_name])
                    element.text = value.isoformat()
                else:
                    element = ElementTree.SubElement(description, FIELD_TO_DC_ELEMENT[field_name])
                    element.text = str(value)
        return ElementTree.tostring(rdf_root, encoding="unicode", method="xml")

    @staticmethod
    def from_rdf(rdf_data: str) -> DublinCoreDocument:
        """Load a DublinCoreDocument from RDF/XML data."""
        root = ElementTree.fromstring(rdf_data)
        dc_data: Dict[str, Any] = {}
        for field_name, dc_element in FIELD_TO_DC_ELEMENT.items():
            elements = root.findall(f".//*/{dc_element}", XML_NAMESPACES)
            if elements:
                texts = [cast(str, elem.text) for elem in elements]
                if len(texts) > 1 and field_name in {"creator", "subject", "contributor"}:
                    dc_data[field_name] = texts
                else:
                    dc_data[field_name] = texts[0]
        document = DublinCoreDocument(**dc_data)
        document.normalize_dates()
        return document

    def to_pickle_bytes(self) -> bytes:
        """Serialize the Dublin Core document to a pickle byte string."""
        if COMPRESSION_TYPE == "zlib":
            return zlib.compress(pickle.dumps(self))
        if COMPRESSION_TYPE == "lzma":
            return lzma.compress(pickle.dumps(self))
        return pickle.dumps(self)

    @staticmethod
    def from_pickle_bytes(pickle_bytes: bytes) -> DublinCoreDocument:
        """Load a DublinCoreDocument from a pickle byte string."""
        if COMPRESSION_TYPE == "zlib":
            return pickle.loads(zlib.decompress(pickle_bytes))
        if COMPRESSION_TYPE == "lzma":
            return pickle.loads(lzma.decompress(pickle_bytes))
        return pickle.loads(pickle_bytes)

    def to_pickle_file(self, file_path: str) -> None:
        """Serialize the Dublin Core document to a pickle file."""
        with open(file_path, "wb") as output_file:
            output_file.write(self.to_pickle_bytes())

    @staticmethod
    def from_pickle_file(file_path: str) -> DublinCoreDocument:
        """Load a DublinCoreDocument from a pickle file."""
        with open(file_path, "rb") as input_file:
            return DublinCoreDocument.from_pickle_bytes(input_file.read())

    @staticmethod
    def _default_serializer(obj: Any) -> str:
        """Serialize datetime objects to ISO format."""
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    @staticmethod
    def from_terms(terms: Dict[str, Any]) -> DublinCoreDocument:
        """Create a DublinCoreDocument from a mapping of Dublin Core terms."""
        data: Dict[str, Any] = {}
        for term, value in terms.items():
            field_name = DC_ELEMENT_TO_FIELD.get(term)
            if not field_name:
                continue
            if field_name in {"creator", "subject", "contributor"} and isinstance(value, str):
                data[field_name] = [value]
            else:
                data[field_name] = value
        document = DublinCoreDocument(**data)
        document.normalize_dates()
        return document

    def to_terms(self) -> Dict[str, Any]:
        """Return the document as a mapping keyed by Dublin Core terms."""
        out: Dict[str, Any] = {}
        for field_name, value in self.to_min_dict().items():
            if field_name not in FIELD_TO_DC_ELEMENT:
                continue
            if isinstance(value, (datetime.date, datetime.datetime)):
                if isinstance(value, datetime.datetime) and value.time() == datetime.time(0, 0):
                    out_value = value.date().isoformat()
                else:
                    out_value = value.isoformat()
            else:
                out_value = value
            out[FIELD_TO_DC_ELEMENT[field_name]] = out_value
        return out
```

### `data/sec-form-10q/sec-form-10q.prompt.yaml`
```text
name: SEC Form 10-Q KPIs
description: Extract key financial metrics from SEC Form 10-Q sections.
model: openai/gpt-4o-mini
modelParameters:
  temperature: 0
messages:
  - role: system
    content: |-
      You are a data-extraction assistant. Given a Form 10-Q section, return key quarterly metrics in JSON.
  - role: user
    content: |-
      Extract the following fields from the text:
      - revenue (USD)
      - operating_income (USD)
      - net_income (USD)
      - total_assets (USD)
```

### `.github/workflows/doc-analysis.prompt.yaml`
```text
name: Document summary
description: Summarize Markdown documents into three bullet points.
model: openai/gpt-4o-mini
modelParameters:
  temperature: 0
messages:
  - role: system
    content: |-
      You analyze Markdown documents and return a short summary.
  - role: user
    content: |-
      Summarize the following document in three bullet points.
```

### `data/sec-form-4/sec-form-4.prompt.yaml`
```text
name: SEC Form 4 transaction extraction
description: Parse SEC Form 4 filings and output structured transactions.
model: openai/gpt-4o-mini
modelParameters:
  temperature: 0
messages:
  - role: system
    content: |-
      You parse SEC Form 4 filings and output structured transactions.
  - role: user
    content: |-
      Extract the following fields from the text:
      - insider_name (string)
      - relationship (string)
      - transaction_date (string)
      - security (string)
      - transaction_type (string)
      - shares (integer)
      - price (number)
```

### `.github/workflows/pr-review.prompt.yaml`
```text
name: Pull request review
description: Provide concise review comments for pull requests.
model: openai/gpt-4o-mini
modelParameters:
  temperature: 0
messages:
  - role: system
    content: |-
      You are a code reviewer. Provide concise review comments.
  - role: user
    content: |-
      Review the following pull request description and suggest improvements.
```

### `data/sec-form-8k/sec-form-8k.prompt.yaml`
```text
name: SEC Form 8-K summary
description: Extract structured event details from SEC Form 8-K filings.
model: openai/gpt-4o-mini
modelParameters:
  temperature: 0
messages:
  - role: system
    content: |-
      You are a SEC filing assistant. Given a Form 8-K section, summarize the event.
  - role: user
    content: |-
      Extract the following fields from the text:
      - event_type (string)
      - event_date (string)
      - summary (string)
```

### `.github/workflows/validate-output.prompt.yaml`
```text
name: Validate Rendered Output
description: Compare original documents with their rendered representation.
model: openai/gpt-4o-mini
modelParameters:
  temperature: 0
messages:
  - role: system
    content: |-
      You verify that a converted document representation matches the original.
  - role: user
    content: |-
      Compare the provided PDF and {format} content. Respond with JSON {"match": bool, "reason": string?}.
```

### `scripts/build_vector_store.py`
```text
import argparse
from pathlib import Path

from ai_doc_analysis_starter.github import build_vector_store


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Directory containing Markdown files")
    args = parser.parse_args()
    build_vector_store(args.source)
```

### `scripts/convert.py`
```text
import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from ai_doc_analysis_starter import OutputFormat, convert_files, suffix_for_format

load_dotenv()


def convert_path(source: Path, formats: list[OutputFormat]) -> None:
    """Convert a file or all files under a directory in-place."""

    def handle_file(file: Path) -> None:
        outputs = {
            fmt: file.with_suffix(suffix_for_format(fmt)) for fmt in formats
        }
        convert_files(file, outputs)

    if source.is_file():
        handle_file(source)
    else:
        for file in source.rglob("*"):
            if file.is_file():
                handle_file(file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Path to raw document or folder")
    parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        help="Desired output format(s). Can be passed multiple times.\n"
        "If omitted, the OUTPUT_FORMATS environment variable or Markdown is used.",
    )
    args = parser.parse_args()

    in_path = Path(args.source)

    def parse_formats(values: list[str]) -> list[OutputFormat]:
        formats: list[OutputFormat] = []
        for val in values:
            try:
                formats.append(OutputFormat(val.strip()))
            except ValueError as exc:  # provide clearer error message
                valid = ", ".join(f.value for f in OutputFormat)
                raise SystemExit(f"Invalid output format '{val}'. Choose from: {valid}") from exc
        return formats

    if args.formats:
        fmts = parse_formats(args.formats)
    elif os.getenv("OUTPUT_FORMATS"):
        fmts = parse_formats(os.getenv("OUTPUT_FORMATS").split(","))
    else:
        fmts = [OutputFormat.MARKDOWN]

    convert_path(in_path, fmts)
```

### `scripts/merge_pr.py`
```text
"""CLI helper to merge pull requests via the GitHub CLI."""

import argparse

from ai_doc_analysis_starter.github import merge_pr


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pr_number", type=int)
    args = parser.parse_args()
    merge_pr(args.pr_number)
```

### `scripts/review_pr.py`
```text
import argparse
import os
from pathlib import Path

from ai_doc_analysis_starter.github import review_pr


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", type=Path, help="Path to pr-review.prompt.yaml")
    parser.add_argument("pr_body", help="Pull request description")
    parser.add_argument(
        "--model",
        default=os.getenv("PR_REVIEW_MODEL"),
        help="Model name override",
    )
    args = parser.parse_args()
    print(review_pr(args.pr_body, args.prompt, model=args.model))
```

### `scripts/run_analysis.py`
```text
import argparse
import os
from pathlib import Path

from ai_doc_analysis_starter.github import run_prompt
from ai_doc_analysis_starter.metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", type=Path)
    parser.add_argument("markdown_doc", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file; defaults to <doc>.<prompt>.json next to the source",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("ANALYZE_MODEL"),
        help="Model name override",
    )
    args = parser.parse_args()

    prompt_name = args.prompt.name.replace(".prompt.yaml", "")
    step_name = "analysis"

    meta = load_metadata(args.markdown_doc)
    file_hash = compute_hash(args.markdown_doc)
    if meta.blake2b == file_hash and is_step_done(meta, step_name):
        raise SystemExit(0)
    if meta.blake2b != file_hash:
        meta.blake2b = file_hash
        meta.extra = {}

    result = run_prompt(
        args.prompt, args.markdown_doc.read_text(), model=args.model
    )
    out_path = (
        args.output
        if args.output
        else args.markdown_doc.with_suffix(f".{prompt_name}.json")
    )
    out_path.write_text(result + "\n", encoding="utf-8")
    mark_step(meta, step_name)
    save_metadata(args.markdown_doc, meta)
```

### `scripts/validate.py`
```text
import argparse
import os
from pathlib import Path

from ai_doc_analysis_starter import OutputFormat
from ai_doc_analysis_starter.github import validate_file
from ai_doc_analysis_starter.metadata import (
    compute_hash,
    is_step_done,
    load_metadata,
    mark_step,
    save_metadata,
)


def infer_format(path: Path) -> OutputFormat:
    mapping = {
        ".md": OutputFormat.MARKDOWN,
        ".html": OutputFormat.HTML,
        ".json": OutputFormat.JSON,
        ".txt": OutputFormat.TEXT,
        ".doctags": OutputFormat.DOCTAGS,
    }
    try:
        return mapping[path.suffix]
    except KeyError as exc:
        valid = ", ".join(mapping.keys())
        raise SystemExit(f"Unknown file extension '{path.suffix}'. Expected one of: {valid}") from exc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("rendered", type=Path)
    parser.add_argument("--format", choices=[f.value for f in OutputFormat])
    parser.add_argument(
        "--prompt",
        type=Path,
        default=Path(".github/workflows/validate-output.prompt.yaml"),
    )
    parser.add_argument(
        "--model",
        default=os.getenv("VALIDATE_MODEL"),
        help="Model name override",
    )
    args = parser.parse_args()

    meta = load_metadata(args.raw)
    file_hash = compute_hash(args.raw)
    if meta.blake2b == file_hash and is_step_done(meta, "validation"):
        raise SystemExit(0)
    if meta.blake2b != file_hash:
        meta.blake2b = file_hash
        meta.extra = {}
    fmt = OutputFormat(args.format) if args.format else infer_format(args.rendered)
    verdict = validate_file(
        args.raw, args.rendered, fmt, args.prompt, model=args.model
    )
    if not verdict.get("match", False):
        raise SystemExit(f"Mismatch detected: {verdict}")
    mark_step(meta, "validation")
    save_metadata(args.raw, meta)
```

### `docs/docusaurus.config.js`
```text
// @ts-check

import {themes as prismThemes} from 'prism-react-renderer';

const config = {
  title: 'AI Doc Analysis Starter',
  tagline: 'Starter template for AI document analysis',
  url: 'https://YOUR_GITHUB_USERNAME.github.io',
  baseUrl: '/',
  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',
  organizationName: 'YOUR_GITHUB_USERNAME',
  projectName: 'ai-doc-analysis-starter',
  presets: [
    [
      'classic',
      ({
        docs: {
          path: 'content',
          sidebarPath: require.resolve('./sidebars.js'),
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],
  themeConfig: {
    navbar: {
      title: 'AI Doc Analysis Starter',
    },
    footer: {
      style: 'dark',
      copyright: `Copyright © ${new Date().getFullYear()} AI Doc Analysis Starter`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  },
};

export default config;
```

### `docs/package.json`
```text
{
  "name": "ai-doc-analysis-starter-docs",
  "private": true,
  "version": "0.0.0",
  "scripts": {
    "start": "docusaurus start",
    "build": "docusaurus build",
    "deploy": "docusaurus deploy",
    "serve": "docusaurus serve"
  },
  "dependencies": {
    "@docusaurus/core": "^3.3.2",
    "@docusaurus/preset-classic": "^3.3.2",
    "prism-react-renderer": "^2.3.0"
  }
}
```

### `docs/content/intro.md`
```text
---
sidebar_position: 1
---

# Introduction

Welcome to the AI Doc Analysis Starter template. This site is built with Docusaurus and documents how to use the repository.
```

### `docs/sidebars.js`
```text
export default {
  tutorialSidebar: [{type: 'autogenerated', dirName: '.'}],
};
```

### `docs/src/css/custom.css`
```text
/* Custom styles for Docusaurus */
```

### `.github/workflows/analysis.yaml`
```text
name: Analysis
on:
  workflow_dispatch:
  push:
    paths:
      - "data/**/*.md"
      - "data/**/*.prompt.yaml"
jobs:
  analysis:
    runs-on: ubuntu-latest
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    steps:
      - uses: actions/checkout@v4
      - name: Load env
        id: env
        uses: ./.github/actions/load-env
        with:
          enable-workflow: ENABLE_PROMPT_ANALYSIS_WORKFLOW
      - name: Setup Python
        if: steps.env.outputs.skip != 'true'
        uses: ./.github/actions/setup-python
        with:
          packages: openai pyyaml
      - name: Run analysis
        if: steps.env.outputs.skip != 'true'
        uses: ./.github/actions/run-analysis
      - uses: actions/upload-artifact@v4
        if: steps.env.outputs.skip != 'true'
        with:
          name: prompt-results
          path: data/**/*.json
```

### `.github/workflows/auto-merge.yaml`
```text
name: Auto Merge
on:
  issue_comment:
jobs:
  auto-merge:
    if: startsWith(github.event.comment.body, '/merge')
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    steps:
      - name: Load env
        id: env
        run: |
          if [ -f .env ]; then
            while IFS='=' read -r key value; do
              if [[ -z "$key" || "$key" == \#* ]]; then
                continue
              fi
              if [ -z "${!key}" ]; then
                echo "$key=$value" >> $GITHUB_ENV
                export "$key=$value"
              fi
            done < .env
          fi
          if [ "${DISABLE_ALL_WORKFLOWS}" = "true" ] || [ "${ENABLE_AUTO_MERGE_WORKFLOW}" != "true" ]; then
            echo "skip=true" >> $GITHUB_OUTPUT
          fi
      - uses: actions/checkout@v4
        if: steps.env.outputs.skip != 'true'
      - uses: actions/setup-python@v5
        if: steps.env.outputs.skip != 'true'
        with: {python-version: '3.x'}
      - name: Approve PR
        if: steps.env.outputs.skip != 'true'
        run: gh pr review ${{ github.event.issue.number }} --approve
      - run: python scripts/merge_pr.py ${{ github.event.issue.number }}
        if: steps.env.outputs.skip != 'true'
```

### `.github/workflows/convert.yaml`
```text
name: Convert
on:
  push:
    paths: ["data/**/*.pdf"]
jobs:
  convert:
    runs-on: ubuntu-latest
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    steps:
      - name: Load env
        id: env
        run: |
          if [ -f .env ]; then
            while IFS='=' read -r key value; do
              if [[ -z "$key" || "$key" == \#* ]]; then
                continue
              fi
              if [ -z "${!key}" ]; then
                echo "$key=$value" >> $GITHUB_ENV
                export "$key=$value"
              fi
            done < .env
          fi
          if [ "${DISABLE_ALL_WORKFLOWS}" = "true" ] || [ "${ENABLE_CONVERT_WORKFLOW}" != "true" ]; then
            echo "skip=true" >> $GITHUB_OUTPUT
          fi
      - uses: actions/checkout@v4
        if: steps.env.outputs.skip != 'true'
      - uses: actions/setup-python@v5
        if: steps.env.outputs.skip != 'true'
        with: {python-version: "3.x"}
      - run: pip install docling
        if: steps.env.outputs.skip != 'true'
      - run: |
          files=$(git diff --name-only ${{ github.event.before }} ${{ github.sha }} -- 'data/**/*.pdf')
          for f in $files; do
            python scripts/convert.py "$f"
          done
        if: steps.env.outputs.skip != 'true'
      - name: Commit conversions
        if: steps.env.outputs.skip != 'true'
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add data
          git commit -m "docs: auto-convert documents" || echo "No changes"
          git push
```

### `.github/workflows/docs.yaml`
```text
name: Docs
on:
  push:
    branches: [main]
    paths:
      - 'docs/**'

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    steps:
      - name: Load env
        id: env
        run: |
          if [ -f .env ]; then
            while IFS='=' read -r key value; do
              if [[ -z "$key" || "$key" == \#* ]]; then
                continue
              fi
              if [ -z "${!key}" ]; then
                echo "$key=$value" >> $GITHUB_ENV
                export "$key=$value"
              fi
            done < .env
          fi
          if [ "${DISABLE_ALL_WORKFLOWS}" = "true" ] || [ "${ENABLE_DOCS_WORKFLOW}" != "true" ]; then
            echo "skip=true" >> $GITHUB_OUTPUT
          fi
      - uses: actions/checkout@v4
        if: steps.env.outputs.skip != 'true'
      - uses: actions/setup-node@v4
        if: steps.env.outputs.skip != 'true'
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: docs/package-lock.json
      - run: npm ci
        if: steps.env.outputs.skip != 'true'
        working-directory: docs
      - run: npm run build
        if: steps.env.outputs.skip != 'true'
        working-directory: docs
      - uses: actions/upload-pages-artifact@v4
        if: steps.env.outputs.skip != 'true'
        with:
          path: docs/build
      - id: deployment
        if: steps.env.outputs.skip != 'true'
        uses: actions/deploy-pages@v4
```

### `.github/workflows/pr-review.yaml`
```text
name: PR Review
on:
  pull_request:
  workflow_dispatch:
    inputs:
      model:
        description: Model name to use
        required: false
        default: gpt-4.1
jobs:
  review:
    runs-on: ubuntu-latest
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    steps:
      - name: Load env
        id: env
        run: |
          if [ -f .env ]; then
            while IFS='=' read -r key value; do
              if [[ -z "$key" || "$key" == \#* ]]; then
                continue
              fi
              if [ -z "${!key}" ]; then
                echo "$key=$value" >> $GITHUB_ENV
                export "$key=$value"
              fi
            done < .env
          fi
          if [ "${DISABLE_ALL_WORKFLOWS}" = "true" ] || [ "${ENABLE_PR_REVIEW_WORKFLOW}" != "true" ]; then
            echo "skip=true" >> $GITHUB_OUTPUT
          fi
      - uses: actions/checkout@v4
        if: steps.env.outputs.skip != 'true'
      - uses: actions/setup-python@v5
        if: steps.env.outputs.skip != 'true'
        with: {python-version: "3.x"}
      - run: pip install openai pyyaml
        if: steps.env.outputs.skip != 'true'
      - name: Review PR
        if: steps.env.outputs.skip != 'true'
        id: review
        env:
          PR_BODY: ${{ github.event.pull_request.body }}
          MODEL: ${{ github.event.inputs.model || env.PR_REVIEW_MODEL || 'gpt-4.1' }}
        run: |
          python scripts/review_pr.py .github/workflows/pr-review.prompt.yaml "$PR_BODY" --model "$MODEL" | tee pr-review.txt
      - name: Comment on PR
        if: steps.env.outputs.skip != 'true'
        run: |
          body=$(cat pr-review.txt)
          gh api repos/${{ github.repository }}/issues/${{ github.event.pull_request.number }}/comments -f body="$body"
```

### `.github/workflows/validate.yaml`
```text
name: Validate Conversions
on:
  push:
    paths:
      - "data/**/*.md"
      - "data/**/*.html"
      - "data/**/*.json"
      - "data/**/*.txt"
      - "data/**/*.doctags"
jobs:
  validate:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    steps:
      - name: Load env
        id: env
        run: |
          if [ -f .env ]; then
            while IFS='=' read -r key value; do
              if [[ -z "$key" || "$key" == \#* ]]; then
                continue
              fi
              if [ -z "${!key}" ]; then
                echo "$key=$value" >> $GITHUB_ENV
                export "$key=$value"
              fi
            done < .env
          fi
          if [ "${DISABLE_ALL_WORKFLOWS}" = "true" ] || [ "${ENABLE_VALIDATE_WORKFLOW}" != "true" ]; then
            echo "skip=true" >> $GITHUB_OUTPUT
          fi
      - uses: actions/checkout@v4
        if: steps.env.outputs.skip != 'true'
      - uses: actions/setup-python@v5
        if: steps.env.outputs.skip != 'true'
        with: {python-version: "3.x"}
      - run: pip install docling openai pyyaml
        if: steps.env.outputs.skip != 'true'
      - run: |
          for file in $(git diff --name-only HEAD~1 -- 'data/**/*.md' 'data/**/*.html' 'data/**/*.json' 'data/**/*.txt' 'data/**/*.doctags'); do
            raw=${file%.*}.pdf
            fmt=${file##*.}
            python scripts/validate.py $raw $file --prompt .github/workflows/validate-output.prompt.yaml || (
              git checkout -- $file
              python scripts/convert.py $raw --format $fmt
              git add $file
            )
          done
        if: steps.env.outputs.skip != 'true'
      - name: Create PR if fixes
        if: steps.env.outputs.skip != 'true'
        run: |
          git diff --staged --quiet && exit 0
          branch="fix-conversion-$(date +%s)"
          git checkout -b "$branch"
          git commit -m "docs: fix document conversion"
          git push origin "$branch"
          gh pr create --fill --title "Fix document conversion" --body "Auto-corrected mismatched output."
```

### `.github/workflows/vector.yaml`
```text
name: Build Vectors
on:
  push:
    branches: [main]
    paths: ["data/**/*.md"]
jobs:
  vectors:
    runs-on: ubuntu-latest
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    steps:
      - name: Load env
        id: env
        run: |
          if [ -f .env ]; then
            while IFS='=' read -r key value; do
              if [[ -z "$key" || "$key" == \#* ]]; then
                continue
              fi
              if [ -z "${!key}" ]; then
                echo "$key=$value" >> $GITHUB_ENV
                export "$key=$value"
              fi
            done < .env
          fi
          if [ "${DISABLE_ALL_WORKFLOWS}" = "true" ] || [ "${ENABLE_VECTOR_WORKFLOW}" != "true" ]; then
            echo "skip=true" >> $GITHUB_OUTPUT
          fi
      - uses: actions/checkout@v4
        if: steps.env.outputs.skip != 'true'
      - uses: actions/setup-python@v5
        if: steps.env.outputs.skip != 'true'
        with: {python-version: '3.x'}
      - run: pip install requests python-dotenv
        if: steps.env.outputs.skip != 'true'
      - run: python scripts/build_vector_store.py data
        if: steps.env.outputs.skip != 'true'
      - name: Commit vectors
        if: steps.env.outputs.skip != 'true'
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add data
          git commit -m "chore: update vectors" || echo "No changes"
          git push
```

