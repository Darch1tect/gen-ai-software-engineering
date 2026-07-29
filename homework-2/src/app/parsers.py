"""Parsers that turn uploaded CSV/JSON/XML bytes into raw ticket dicts.

Each parser returns a list of dicts shaped like the TicketCreate schema.
Validation is NOT done here — records are validated one by one during import
so a single bad record does not fail the whole file.
"""

import csv
import io
import json
from typing import Any
from xml.etree import ElementTree

MAX_IMPORT_RECORDS = 10_000

CSV_METADATA_FIELDS = ("source", "browser", "device_type")


class FileParseError(Exception):
    """The file as a whole is malformed and no records can be extracted."""


def parse_csv(data: bytes) -> list[dict[str, Any]]:
    text = _decode(data)
    try:
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            raise FileParseError("CSV file is empty: a header row is required")
        rows = list(reader)
    except csv.Error as exc:
        raise FileParseError(f"Malformed CSV: {exc}") from exc

    records = []
    for row in rows:
        # None key collects overflow cells from rows with too many columns
        row.pop(None, None)
        record: dict[str, Any] = {
            k: v for k, v in row.items() if v is not None and v.strip() != ""
        }
        if "tags" in record:
            record["tags"] = [t.strip() for t in record["tags"].split(";") if t.strip()]
        metadata = {f: record.pop(f) for f in CSV_METADATA_FIELDS if f in record}
        if metadata:
            record["metadata"] = metadata
        records.append(record)
    return records


def parse_json(data: bytes) -> list[dict[str, Any]]:
    text = _decode(data)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise FileParseError(f"Malformed JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")

    if isinstance(payload, dict) and isinstance(payload.get("tickets"), list):
        payload = payload["tickets"]
    if not isinstance(payload, list):
        raise FileParseError(
            "JSON must be an array of ticket objects, or an object with a 'tickets' array"
        )
    return [item if isinstance(item, dict) else {"_raw": item} for item in payload]


def parse_xml(data: bytes) -> list[dict[str, Any]]:
    try:
        root = ElementTree.fromstring(_decode(data))
    except ElementTree.ParseError as exc:
        raise FileParseError(f"Malformed XML: {exc}")

    ticket_elements = root.findall("ticket") if root.tag != "ticket" else [root]
    if not ticket_elements:
        raise FileParseError(
            "No <ticket> elements found: expected a <tickets> root with <ticket> children"
        )

    records = []
    for element in ticket_elements:
        record: dict[str, Any] = {}
        for child in element:
            if child.tag == "tags":
                record["tags"] = [
                    tag.text.strip() for tag in child.findall("tag") if tag.text and tag.text.strip()
                ]
            elif child.tag == "metadata":
                record["metadata"] = {
                    m.tag: m.text.strip() for m in child if m.text and m.text.strip()
                }
            elif child.text is not None and child.text.strip() != "":
                record[child.tag] = child.text.strip()
        records.append(record)
    return records


PARSERS = {
    "csv": parse_csv,
    "json": parse_json,
    "xml": parse_xml,
}

CONTENT_TYPE_FORMATS = {
    "text/csv": "csv",
    "application/csv": "csv",
    "application/json": "json",
    "text/json": "json",
    "application/xml": "xml",
    "text/xml": "xml",
}


def detect_format(filename: str | None, content_type: str | None) -> str | None:
    if filename and "." in filename:
        extension = filename.rsplit(".", 1)[1].lower()
        if extension in PARSERS:
            return extension
    if content_type:
        return CONTENT_TYPE_FORMATS.get(content_type.split(";")[0].strip().lower())
    return None


def parse_file(data: bytes, file_format: str) -> list[dict[str, Any]]:
    records = PARSERS[file_format](data)
    if len(records) > MAX_IMPORT_RECORDS:
        raise FileParseError(
            f"File contains {len(records)} records; the limit per import is {MAX_IMPORT_RECORDS}"
        )
    return records


def _decode(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise FileParseError("File is not valid UTF-8 text") from exc
