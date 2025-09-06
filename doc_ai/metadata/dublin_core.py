"""Dublin Core metadata utilities."""

# mypy: ignore-errors
from __future__ import annotations

import base64
import binascii
import datetime
import json
import logging
import lzma
import pickle
import uuid
import zlib
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional, cast
from xml.etree import ElementTree

COMPRESSION_TYPE: Optional[Literal["zlib", "lzma"]] = "zlib"

logger = logging.getLogger(__name__)

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
        except (binascii.Error, lzma.LZMAError, zlib.error) as exc:
            logger.warning("Failed to decode content: %s", exc)
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
                    element = ElementTree.SubElement(
                        root_element, FIELD_TO_DC_ELEMENT[field_name]
                    )
                    element.text = value.isoformat()
                else:
                    element = ElementTree.SubElement(
                        root_element, FIELD_TO_DC_ELEMENT[field_name]
                    )
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
                if len(texts) > 1 and field_name in {
                    "creator",
                    "subject",
                    "contributor",
                }:
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
                    element = ElementTree.SubElement(
                        description, FIELD_TO_DC_ELEMENT[field_name]
                    )
                    element.text = value.isoformat()
                else:
                    element = ElementTree.SubElement(
                        description, FIELD_TO_DC_ELEMENT[field_name]
                    )
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
                if len(texts) > 1 and field_name in {
                    "creator",
                    "subject",
                    "contributor",
                }:
                    dc_data[field_name] = texts
                else:
                    dc_data[field_name] = texts[0]
        document = DublinCoreDocument(**dc_data)
        document.normalize_dates()
        return document

    def to_pickle_bytes(self) -> bytes:
        """Serialize the Dublin Core document to a pickle byte string.

        Warning:
            This uses Python's ``pickle`` module which is not secure against
            code execution during loading. Only use this for data generated by
            trusted parties. For untrusted or public data, prefer
            :meth:`to_json`.
        """
        if COMPRESSION_TYPE == "zlib":
            return zlib.compress(pickle.dumps(self))
        if COMPRESSION_TYPE == "lzma":
            return lzma.compress(pickle.dumps(self))
        return pickle.dumps(self)

    @staticmethod
    def from_pickle_bytes(
        pickle_bytes: bytes, *, unsafe: bool = False
    ) -> DublinCoreDocument:
        """Load a DublinCoreDocument from a pickle byte string.

        Warning:
            Unpickling data from untrusted sources can execute arbitrary code.
            By default this method refuses to load the provided bytes. Pass
            ``unsafe=True`` to explicitly acknowledge the risk. When possible,
            use :meth:`from_json` for safer deserialization of external data.
        """
        if not unsafe:
            raise ValueError(
                "Unpickling arbitrary data is unsafe. Set unsafe=True to proceed."
            )
        if COMPRESSION_TYPE == "zlib":
            return pickle.loads(zlib.decompress(pickle_bytes))
        if COMPRESSION_TYPE == "lzma":
            return pickle.loads(lzma.decompress(pickle_bytes))
        return pickle.loads(pickle_bytes)

    def to_pickle_file(self, file_path: str) -> None:
        """Serialize the Dublin Core document to a pickle file.

        Warning:
            The resulting file should only be loaded in trusted environments.
            Consider :meth:`to_json` for a safer, interoperable format.
        """
        with open(file_path, "wb") as output_file:
            output_file.write(self.to_pickle_bytes())

    @staticmethod
    def from_pickle_file(file_path: str, *, unsafe: bool = False) -> DublinCoreDocument:
        """Load a DublinCoreDocument from a pickle file.

        Warning:
            Unpickling data from untrusted sources can execute arbitrary code.
            This method requires ``unsafe=True`` to proceed. Prefer
            :meth:`from_json` when loading external data.
        """
        with open(file_path, "rb") as input_file:
            return DublinCoreDocument.from_pickle_bytes(
                input_file.read(), unsafe=unsafe
            )

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
            if field_name in {"creator", "subject", "contributor"} and isinstance(
                value, str
            ):
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
                if isinstance(
                    value, datetime.datetime
                ) and value.time() == datetime.time(0, 0):
                    out_value = value.date().isoformat()
                else:
                    out_value = value.isoformat()
            else:
                out_value = value
            out[FIELD_TO_DC_ELEMENT[field_name]] = out_value
        return out
