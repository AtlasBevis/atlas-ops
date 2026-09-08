#!/usr/bin/env python3
"""Build Key / Value (Envelope) versions from groups/<groupId>/ trees.

Layout:
  groups/<groupId>/spec.yaml
  groups/<groupId>/<table>/keys/v<N>.yaml
  groups/<groupId>/<table>/values/v<N>.yaml

Value is the Debezium Envelope. Inner row record is inlined as `Value`.
References are derived from source.type + source.database, not from spec.yaml:
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
from groups.group import discover_group_specs

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
class GroupFolderSpec:
    path: Path
    group_id: str
    db_schema: str
    topic_prefix: str
    connector: str
    tables: tuple[TableSpec, ...]


def _version_filename(version: str) -> str:
    v = version.strip()
    if v.lower().startswith("v"):
        return f"{v}.yaml"
    return f"v{v}.yaml"


def _table_dir(group_dir: Path, table_name: str) -> Path:
    wanted = table_name.lower()
    for child in group_dir.iterdir():
        if child.is_dir() and child.name.lower() == wanted:
            return child
    raise FileNotFoundError(
        f"Table folder for '{table_name}' not found under {group_dir}"
    )


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


def load_group_folder(spec_path: Path) -> GroupFolderSpec:
    data = load_yaml(spec_path)
    group_id = require(data, "groupId", spec_path)
    source = require(data, "source", spec_path)
    if not isinstance(source, dict):
        raise ValueError(f"'source' must be an object in {spec_path}")
    source_type = source.get("type")
    if source_type != "debezium":
        raise ValueError(f"'source.type' must be 'debezium' in {spec_path}")
    connector = source.get("database")
    if not isinstance(connector, str) or not connector.strip():
        raise ValueError(f"'source.database' is required in {spec_path}")
    connector_source_artifact_id(str(connector))

    raw_tables = require(data, "tables", spec_path)
    if not isinstance(raw_tables, list) or not raw_tables:
        raise ValueError(f"'tables' must be a non-empty list in {spec_path}")

    tables: list[TableSpec] = []
    seen: set[str] = set()
    for i, entry in enumerate(raw_tables):
        if not isinstance(entry, dict):
            raise ValueError(f"tables[{i}] must be an object in {spec_path}")
        name = require(entry, "name", spec_path)
        if name in seen:
            raise ValueError(f"Duplicate table '{name}' in {spec_path}")
        seen.add(name)
        key_desc, key_versions = _parse_side(
            require(entry, "key", spec_path),
            path=spec_path,
            loc=f"tables[{i}].key",
        )
        value_desc, value_versions = _parse_side(
            require(entry, "value", spec_path),
            path=spec_path,
            loc=f"tables[{i}].value",
        )
        tables.append(
            TableSpec(
                name=name,
                description=entry.get("description"),
                key_description=key_desc,
                value_description=value_desc,
                key_versions=key_versions,
                value_versions=value_versions,
            )
        )

    return GroupFolderSpec(
        path=spec_path,
        group_id=group_id,
        db_schema=require(data, "schema", spec_path),
        topic_prefix=require(data, "topicPrefix", spec_path),
        connector=str(connector),
        tables=tuple(tables),
    )


def load_group_folders() -> list[GroupFolderSpec]:
    if not GROUPS_ROOT.is_dir():
        return []
    return [load_group_folder(p) for p in discover_group_specs()]


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


def _record_namespace(spec: GroupFolderSpec, table_name: str) -> str:
    return f"{spec.topic_prefix}.{spec.db_schema}.{table_name}"


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
    folders = load_group_folders()
    created = 0
    versioned = 0
    skipped = 0

    for spec in folders:
        existing = list_artifacts(base, spec.group_id)
        group_dir = spec.path.parent
        for table in spec.tables:
            table_dir = _table_dir(group_dir, table.name)
            ns = _record_namespace(spec, table.name)
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
        f"[tables] groups={len(folders)} created={created} "
        f"versions={versioned} skipped={skipped}"
    )
