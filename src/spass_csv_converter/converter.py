from __future__ import annotations

import csv
import gzip
import io
import json
import plistlib
import sqlite3
import tempfile
import zipfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


class ConversionError(Exception):
    """Raised when a .spass file cannot be converted."""


@dataclass(frozen=True)
class ConversionResult:
    output_path: Path
    row_count: int
    warnings: tuple[str, ...] = ()


COMMON_FIELD_ORDER = [
    "title",
    "name",
    "app",
    "appName",
    "service",
    "url",
    "website",
    "domain",
    "username",
    "userName",
    "login",
    "email",
    "password",
    "pass",
    "notes",
    "memo",
    "created",
    "createdAt",
    "updated",
    "updatedAt",
    "source_path",
    "source_table",
]


def convert_spass_to_csv(input_path: Path | str, output_path: Path | str) -> ConversionResult:
    input_path = Path(input_path).expanduser()
    output_path = Path(output_path).expanduser()

    if not input_path.exists():
        raise ConversionError(f"File not found: {input_path}")

    data = input_path.read_bytes()
    warnings: list[str] = []
    records = _extract_records(input_path, data, warnings)
    if not records:
        raise ConversionError(
            "No readable records were found. This .spass file may be encrypted or use a "
            "Samsung-proprietary format. Try exporting from Samsung Pass again and check "
            "whether the app offers CSV export or password-protected export options."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = _ordered_fieldnames(records)
    with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    return ConversionResult(output_path=output_path, row_count=len(records), warnings=tuple(warnings))


def _extract_records(path: Path, data: bytes, warnings: list[str]) -> list[dict[str, str]]:
    for decoder in (_maybe_gzip, lambda value: value):
        try:
            decoded = decoder(data)
        except OSError:
            continue
        records = _extract_plain_records(path.name, decoded, warnings)
        if records:
            return records
    return []


def _extract_plain_records(source_name: str, data: bytes, warnings: list[str]) -> list[dict[str, str]]:
    if zipfile.is_zipfile(io.BytesIO(data)):
        return _extract_zip_records(data, warnings)

    parsers = (
        _records_from_json,
        _records_from_plist,
        _records_from_csv,
        _records_from_xml,
    )
    for parser in parsers:
        records = parser(source_name, data)
        if records:
            return records

    sqlite_records = _records_from_sqlite_bytes(source_name, data, warnings)
    if sqlite_records:
        return sqlite_records

    return []


def _maybe_gzip(data: bytes) -> bytes:
    if data[:2] != b"\x1f\x8b":
        raise OSError("not gzip")
    return gzip.decompress(data)


def _extract_zip_records(data: bytes, warnings: list[str]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            file_data = archive.read(info)
            inner_records = _extract_plain_records(info.filename, file_data, warnings)
            for record in inner_records:
                record.setdefault("source_path", info.filename)
            records.extend(inner_records)
    return records


def _records_from_json(source_name: str, data: bytes) -> list[dict[str, str]]:
    text = _decode_text(data)
    if not text:
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    records = [_stringify_record(record) for record in _find_dict_records(payload)]
    return _with_source(records, source_name)


def _records_from_plist(source_name: str, data: bytes) -> list[dict[str, str]]:
    try:
        payload = plistlib.loads(data)
    except Exception:
        return []
    records = [_stringify_record(record) for record in _find_dict_records(payload)]
    return _with_source(records, source_name)


def _records_from_csv(source_name: str, data: bytes) -> list[dict[str, str]]:
    text = _decode_text(data)
    if not text or "," not in text:
        return []
    try:
        sample = text[:2048]
        dialect = csv.Sniffer().sniff(sample)
        has_header = csv.Sniffer().has_header(sample)
    except csv.Error:
        return []

    reader: Iterable[Mapping[str, Any]]
    stream = io.StringIO(text)
    if has_header:
        reader = csv.DictReader(stream, dialect=dialect)
    else:
        rows = csv.reader(stream, dialect=dialect)
        reader = ({f"column_{index + 1}": value for index, value in enumerate(row)} for row in rows)
    records = [_stringify_record(dict(row)) for row in reader]
    records = [record for record in records if any(record.values())]
    return _with_source(records, source_name)


def _records_from_xml(source_name: str, data: bytes) -> list[dict[str, str]]:
    text = _decode_text(data)
    if not text or "<" not in text:
        return []
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError:
        return []

    records: list[dict[str, str]] = []
    for element in root.iter():
        children = list(element)
        if not children:
            continue
        leaves = {
            child.tag.split("}")[-1]: (child.text or "").strip()
            for child in children
            if not list(child) and (child.text or "").strip()
        }
        if len(leaves) >= 2:
            records.append(_stringify_record(leaves))
    return _with_source(records, source_name)


def _records_from_sqlite_bytes(source_name: str, data: bytes, warnings: list[str]) -> list[dict[str, str]]:
    if not data.startswith(b"SQLite format 3\x00"):
        return []

    with tempfile.NamedTemporaryFile(suffix=".sqlite") as temp:
        temp.write(data)
        temp.flush()
        return _records_from_sqlite_path(source_name, Path(temp.name), warnings)


def _records_from_sqlite_path(source_name: str, db_path: Path, warnings: list[str]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    try:
        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return []

    try:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        for (table_name,) in tables:
            try:
                cursor = connection.execute(f"SELECT * FROM {_quote_identifier(table_name)}")
            except sqlite3.Error as exc:
                warnings.append(f"Skipped table {table_name}: {exc}")
                continue
            columns = [description[0] for description in cursor.description or []]
            for row in cursor.fetchall():
                record = _stringify_record(dict(zip(columns, row, strict=False)))
                record["source_table"] = str(table_name)
                record["source_path"] = source_name
                records.append(record)
    finally:
        connection.close()
    return records


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _find_dict_records(payload: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    _walk(payload, records)
    return records


def _walk(value: Any, records: list[dict[str, Any]]) -> None:
    if isinstance(value, list):
        dict_items = [item for item in value if isinstance(item, dict)]
        if len(dict_items) >= 1:
            for item in dict_items:
                flattened = _flatten_dict(item)
                if len(flattened) >= 2:
                    records.append(flattened)
        for item in value:
            _walk(item, records)
    elif isinstance(value, dict):
        for nested in value.values():
            _walk(nested, records)


def _flatten_dict(value: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, item in value.items():
        field = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(item, Mapping):
            flattened.update(_flatten_dict(item, field))
        elif isinstance(item, list):
            if all(not isinstance(element, (dict, list)) for element in item):
                flattened[field] = "; ".join(str(element) for element in item)
        elif item is not None:
            flattened[field] = item
    return flattened


def _stringify_record(record: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in record.items():
        if value is None:
            result[str(key)] = ""
        elif isinstance(value, bytes):
            result[str(key)] = value.hex()
        else:
            result[str(key)] = str(value)
    return result


def _with_source(records: list[dict[str, str]], source_name: str) -> list[dict[str, str]]:
    for record in records:
        record.setdefault("source_path", source_name)
    return records


def _ordered_fieldnames(records: list[dict[str, str]]) -> list[str]:
    fields = {field for record in records for field in record}
    ordered = [field for field in COMMON_FIELD_ORDER if field in fields]
    ordered.extend(sorted(fields - set(ordered)))
    return ordered


def _decode_text(data: bytes) -> str | None:
    for encoding in ("utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            text = data.decode(encoding)
        except UnicodeDecodeError:
            continue
        if text.strip():
            return text
    return None
