#!/usr/bin/env python3
"""Build Key / Value (Envelope) versions from per-table indexes.

Layout:
  groups/index.yaml
  groups/<groupId>/<table>/index.yaml
  groups/<groupId>/<table>/keys/v<N>.yaml
  groups/<groupId>/<table>/values/v<N>.yaml

Value is the Debezium Envelope. Inner row record is inlined as `Value`.
References are derived from source.type + source.database:
  debezium / io.debezium.connector.<db>.Source @ 1
  debezium / event.block @ 1
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from artifacts.artifact import ensure_artifact_version, list_artifacts
from bootstrap import (
    BOOTSTRAP_VERSION,
    DEBEZIUM_GROUP,
    connector_source_artifact_id,
)
from common import GROUPS_ROOT, load_yaml, require
from groups.group import discover_table_indexes

AVRO_PRIMITIVES = frozenset(
    {"null", "boolean", "int", "long", "float", "double", "bytes", "string"}
)


@dataclass(frozen=True, slots=True)
class VersionSpec:
    version: str
    state: str
    description: str | None


@dataclass(frozen=True, slots=True)
class TableSpec:
    name: str
    description: str | None
    key_description: str | None
    value_description: str | None
    key_versions: tuple[VersionSpec, ...]
    value_versions: tuple[VersionSpec, ...]


@dataclass(frozen=True, slots=True)
class TableIndex:
    path: Path
    group_id: str
    db_schema: str
    topic_prefix: str
    connector: str
    table: TableSpec


def _version_filename(version: str) -> str:
    v = version.strip()
    if v.lower().startswith("v"):
        return f"{v}.yaml"
    return f"v{v}.yaml"


def _parse_version_specs(
    raw: object,
    *,
    path: Path,
    loc: str,
) -> tuple[VersionSpec, ...]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{loc} must be a non-empty list in {path}")
    specs: list[VersionSpec] = []
    seen: set[str] = set()
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise ValueError(f"{loc}[{i}] must be an object in {path}")
        version = str(require(entry, "version", path))
        if version in seen:
            raise ValueError(f"Duplicate version '{version}' in {loc} of {path}")
        seen.add(version)
        specs.append(
            VersionSpec(
                version=version,
                state=str(entry.get("state", "ENABLED")),
                description=entry.get("description"),
            )
        )
    return tuple(specs)


def _parse_side(
    raw: object,
    *,
    path: Path,
    loc: str,
) -> tuple[str | None, tuple[VersionSpec, ...]]:
    if not isinstance(raw, dict):
        raise ValueError(f"{loc} must be an object in {path}")
    versions = _parse_version_specs(
        require(raw, "versions", path),
        path=path,
        loc=f"{loc}.versions",
    )
    description = raw.get("description")
    return description, versions


def load_table_index(spec_path: Path) -> TableIndex:
    data = load_yaml(spec_path)
    group_id = require(data, "groupId", spec_path)
    group_folder = spec_path.parent.parent.name
    if group_id != group_folder:
        raise ValueError(
            f"groupId '{group_id}' must match folder '{group_folder}' in {spec_path}"
        )

    source = require(data, "source", spec_path)
    if not isinstance(source, dict):
        raise ValueError(f"'source' must be an object in {spec_path}")
    if source.get("type") != "debezium":
        raise ValueError(f"'source.type' must be 'debezium' in {spec_path}")
    connector = source.get("database")
    if not isinstance(connector, str) or not connector.strip():
        raise ValueError(f"'source.database' is required in {spec_path}")
    connector_source_artifact_id(str(connector))

    entry = require(data, "table", spec_path)
    if not isinstance(entry, dict):
        raise ValueError(f"'table' must be an object in {spec_path}")
    name = require(entry, "name", spec_path)
    folder_name = spec_path.parent.name
    if name.lower() != folder_name.lower():
        raise ValueError(
            f"table.name '{name}' must match folder '{folder_name}' in {spec_path}"
        )

    key_desc, key_versions = _parse_side(
        require(entry, "key", spec_path),
        path=spec_path,
        loc="table.key",
    )
    value_desc, value_versions = _parse_side(
        require(entry, "value", spec_path),
        path=spec_path,
        loc="table.value",
    )
    table = TableSpec(
        name=name,
        description=entry.get("description"),
        key_description=key_desc,
        value_description=value_desc,
        key_versions=key_versions,
        value_versions=value_versions,
    )
    return TableIndex(
        path=spec_path,
        group_id=group_id,
        db_schema=require(data, "schema", spec_path),
        topic_prefix=require(data, "topicPrefix", spec_path),
        connector=str(connector),
        table=table,
    )


def load_table_indexes() -> list[TableIndex]:
    if not GROUPS_ROOT.is_dir():
        return []
    return [load_table_index(p) for p in discover_table_indexes()]


def _avro_field(entry: dict[str, Any], *, path: Path, default_nullable: bool) -> dict[str, Any]:
    name = require(entry, "name", path)
    avro_type = require(entry, "type", path)
    if not isinstance(avro_type, str) or avro_type not in AVRO_PRIMITIVES:
        allowed = ", ".join(sorted(AVRO_PRIMITIVES - {"null"}))
        raise ValueError(f"Unsupported Avro type '{avro_type}' for '{name}' in {path}. Allowed: {allowed}")
    nullable = entry.get("nullable", default_nullable)
    field: dict[str, Any] = {"name": name}
    if nullable:
        field["type"] = ["null", avro_type]
        field["default"] = None if "default" not in entry else entry.get("default")
    else:
        field["type"] = avro_type
        if "default" in entry:
            field["default"] = entry["default"]
    return field


def _load_fields(path: Path, kind: str) -> list[dict[str, Any]]:
    data = load_yaml(path)
    key = "keys" if kind == "key" else "values"
    rows = require(data, key, path)
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"'{key}' must be a non-empty list in {path}")
    default_nullable = kind != "key"
    fields: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, entry in enumerate(rows):
        if not isinstance(entry, dict):
            raise ValueError(f"{key}[{i}] must be an object in {path}")
        field = _avro_field(entry, path=path, default_nullable=default_nullable)
        if field["name"] in seen:
            raise ValueError(f"Duplicate field '{field['name']}' in {path}")
        seen.add(field["name"])
        fields.append(field)
    return fields


def _record_namespace(spec: TableIndex) -> str:
    return f"{spec.topic_prefix}.{spec.db_schema}.{spec.table.name}"


def key_schema(ns: str, fields: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "record",
        "name": "Key",
        "namespace": ns,
        "fields": fields,
        "connect.name": f"{ns}.Key",
    }


def value_envelope_schema(
    ns: str,
    fields: list[dict[str, Any]],
    source_type: str,
) -> dict[str, Any]:
    value_record: dict[str, Any] = {
        "type": "record",
        "name": "Value",
        "fields": fields,
        "connect.name": f"{ns}.Value",
    }
    return {
        "type": "record",
        "name": "Envelope",
        "namespace": ns,
        "fields": [
            {"name": "before", "type": ["null", value_record], "default": None},
            {"name": "after", "type": ["null", "Value"], "default": None},
            {"name": "source", "type": source_type},
            {"name": "transaction", "type": ["null", "event.block"], "default": None},
            {"name": "op", "type": "string"},
            {"name": "ts_ms", "type": ["null", "long"], "default": None},
            {"name": "ts_us", "type": ["null", "long"], "default": None},
            {"name": "ts_ns", "type": ["null", "long"], "default": None},
        ],
        "connect.version": 2,
        "connect.name": f"{ns}.Envelope",
    }


def default_value_references(connector: str) -> list[dict[str, str]]:
    source_id = connector_source_artifact_id(connector)
    return [
        {
            "name": source_id,
            "groupId": DEBEZIUM_GROUP,
            "artifactId": source_id,
            "version": BOOTSTRAP_VERSION,
        },
        {
            "name": "event.block",
            "groupId": DEBEZIUM_GROUP,
            "artifactId": "event.block",
            "version": BOOTSTRAP_VERSION,
        },
    ]


def _content_path(table_dir: Path, kind: str, version: str) -> Path:
    folder = "keys" if kind == "key" else "values"
    path = table_dir / folder / _version_filename(version)
    if not path.is_file():
        raise FileNotFoundError(f"Missing {kind} version file: {path}")
    return path


def sync_table_artifacts(base: str) -> None:
    indexes = load_table_indexes()
    created = 0
    versioned = 0
    skipped = 0
    existing_by_group: dict[str, set[str]] = {}

    for spec in indexes:
        existing = existing_by_group.get(spec.group_id)
        if existing is None:
            existing = list_artifacts(base, spec.group_id)
            existing_by_group[spec.group_id] = existing

        table = spec.table
        table_dir = spec.path.parent
        ns = _record_namespace(spec)
        source_type = connector_source_artifact_id(spec.connector)

        for ver in table.key_versions:
            content = key_schema(
                ns,
                _load_fields(_content_path(table_dir, "key", ver.version), "key"),
            )
            result = ensure_artifact_version(
                base,
                spec.group_id,
                f"{ns}.Key",
                content,
                version=ver.version,
                existing_artifacts=existing,
                name=f"{ns}.Key",
                description=ver.description or table.key_description,
            )
            if result == "created":
                created += 1
            elif result == "version":
                versioned += 1
            else:
                skipped += 1

        auto_refs = default_value_references(spec.connector)
        for ver in table.value_versions:
            content = value_envelope_schema(
                ns,
                _load_fields(_content_path(table_dir, "value", ver.version), "value"),
                source_type,
            )
            result = ensure_artifact_version(
                base,
                spec.group_id,
                f"{ns}.Value",
                content,
                version=ver.version,
                existing_artifacts=existing,
                name=f"{ns}.Value",
                description=ver.description or table.value_description,
                references=auto_refs,
            )
            if result == "created":
                created += 1
            elif result == "version":
                versioned += 1
            else:
                skipped += 1

    print(
        f"[tables] indexes={len(indexes)} created={created} "
        f"versions={versioned} skipped={skipped}"
    )
