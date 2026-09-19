#!/usr/bin/env python3
"""Parse version lists and CDC / JSON Schema content files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.common import load_yaml, require
from core.references import merge_references, parse_references

from .mapping import map_column
from .models import Version


def version_filename(version: str) -> str:
    v = version.strip()
    if v.lower().startswith("v"):
        return f"{v}.yaml"
    return f"v{v}.yaml"


def parse_version(
    entry: dict,
    *,
    path: Path,
    loc: str,
    content_path: Path | None = None,
) -> Version:
    version = str(require(entry, "version", path))
    if content_path is None:
        content = require(entry, "content", path)
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"{loc}.content must be a non-empty relative path in {path}")
        content_path = (path.parent / content).resolve()
    if not content_path.is_file():
        raise ValueError(f"{loc} content file not found: {content_path}")

    description = entry.get("description")
    state = entry.get("state", "ENABLED")
    refs = parse_references(entry.get("references"), path=path, loc=loc)

    return Version(
        version=version,
        content_path=content_path,
        state=str(state),
        description=description,
        references=refs,
    )


def parse_versions(
    raw: object,
    *,
    path: Path,
    loc: str,
    content_dir: Path | None = None,
) -> tuple[Version, ...]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{loc} must be a non-empty list in {path}")

    specs: list[Version] = []
    seen: set[str] = set()
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise ValueError(f"{loc}[{i}] must be an object in {path}")

        version = str(require(entry, "version", path))
        if version in seen:
            raise ValueError(f"Duplicate version '{version}' in {loc} of {path}")

        seen.add(version)
        resolved = None
        if content_dir is not None:
            resolved = (content_dir / version_filename(version)).resolve()

        specs.append(
            parse_version(
                entry,
                path=path,
                loc=f"{loc}[{i}]",
                content_path=resolved,
            )
        )
    return tuple(specs)


def load_fields(
    path: Path,
    kind: str,
    connector: str,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    data = load_yaml(path)
    key = "keys" if kind == "key" else "values"
    rows = require(data, key, path)
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"'{key}' must be a non-empty list in {path}")
    default_nullable = kind != "key"
    fields: list[dict[str, Any]] = []
    refs: list[dict[str, str]] = []
    seen: set[str] = set()
    for i, entry in enumerate(rows):
        if not isinstance(entry, dict):
            raise ValueError(f"{key}[{i}] must be an object in {path}")
        field, field_refs = map_column(
            entry,
            path=path,
            connector=connector,
            default_nullable=default_nullable,
        )
        if field["name"] in seen:
            raise ValueError(f"Duplicate field '{field['name']}' in {path}")
        seen.add(field["name"])
        fields.append(field)
        refs.extend(field_refs)
    return fields, merge_references(refs)


def load_json_schema(path: Path) -> dict[str, Any]:
    """Load a JSON Schema document stored as YAML (not CDC keys/values lists).

    Root `type` defaults to "object" when omitted — log event payloads
    (key/value) are always JSON objects.
    """
    data = load_yaml(path)
    if "keys" in data or "values" in data:
        raise ValueError(
            f"{path} looks like CDC column YAML; JSON Schema document expected"
        )
    data.setdefault("type", "object")
    return data
