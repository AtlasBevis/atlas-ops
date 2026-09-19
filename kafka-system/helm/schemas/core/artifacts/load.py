#!/usr/bin/env python3
"""Load table indexes from domain/*/*/index.yaml."""

from __future__ import annotations

from pathlib import Path

from core.common import GROUPS_ROOT, load_yaml, require
from core.versions.parse import parse_versions

from .artifact_types import ArtifactType, SourceType, parse_artifact_type, parse_source_type
from .models import TableIndex, TableSpec


def discover_table_indexes() -> list[Path]:
    if not GROUPS_ROOT.is_dir():
        return []
    return sorted(GROUPS_ROOT.glob("*/*/index.yaml"))


def _parse_side(
    raw: object,
    *,
    path: Path,
    loc: str,
    content_dir: Path,
) -> tuple[str | None, tuple]:
    if not isinstance(raw, dict):
        raise ValueError(f"{loc} must be an object in {path}")

    versions = parse_versions(
        require(raw, "versions", path),
        path=path,
        loc=f"{loc}.versions",
        content_dir=content_dir,
    )
    description = raw.get("description")
    return description, versions


def load_table_index(spec_path: Path) -> TableIndex:
    data = load_yaml(spec_path)
    group_id = require(data, "groupId", spec_path)

    source = require(data, "source", spec_path)
    if not isinstance(source, dict):
        raise ValueError(f"'source' must be an object in {spec_path}")

    source_type = parse_source_type(source.get("type"), spec_path)
    artifact_type = parse_artifact_type(
        source, source_type=source_type, path=spec_path
    )

    if source_type is SourceType.LOG:
        if source.get("database"):
            raise ValueError(
                f"'source.database' is not allowed when source.type is log in {spec_path}"
            )
        if source.get("heartbeat"):
            raise ValueError(
                f"'source.heartbeat' is not allowed when source.type is log in {spec_path}"
            )
        prefix = source.get("heartbeatPrefix")
        if isinstance(prefix, str) and prefix.strip():
            raise ValueError(
                f"'source.heartbeatPrefix' is not allowed when source.type is log "
                f"in {spec_path}"
            )
        connector = ""
        heartbeat = False
        heartbeat_prefix = None
    else:
        connector = source.get("database")
        if not isinstance(connector, str) or not connector.strip():
            raise ValueError(f"'source.database' is required in {spec_path}")
        heartbeat = bool(source.get("heartbeat", False))
        prefix = source.get("heartbeatPrefix")
        heartbeat_prefix = (
            prefix.strip() if isinstance(prefix, str) and prefix.strip() else None
        )

    entry = require(data, "table", spec_path)
    if not isinstance(entry, dict):
        raise ValueError(f"'table' must be an object in {spec_path}")

    name = require(entry, "name", spec_path)

    key_raw = entry.get("key")
    if key_raw is None:
        if artifact_type is not ArtifactType.JSON:
            raise ValueError(f"'table.key' is required in {spec_path}")
        key_desc, key_versions = None, ()
    else:
        key_desc, key_versions = _parse_side(
            key_raw,
            path=spec_path,
            loc="table.key",
            content_dir=spec_path.parent / "keys",
        )
    value_desc, value_versions = _parse_side(
        require(entry, "value", spec_path),
        path=spec_path,
        loc="table.value",
        content_dir=spec_path.parent / "values",
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
        source_type=source_type,
        artifact_type=artifact_type,
        connector=str(connector),
        heartbeat=heartbeat,
        heartbeat_prefix=heartbeat_prefix,
        table=table,
    )


def load_table_indexes() -> list[TableIndex]:
    result: list[TableIndex] = []
    for spec_path in discover_table_indexes():
        try:
            result.append(load_table_index(spec_path))
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Failed to load table index {spec_path}: {exc}") from exc
    return result


def filter_table_indexes(
    indexes: list[TableIndex],
    known_groups: set[str],
) -> list[TableIndex]:
    kept: list[TableIndex] = []
    for spec in indexes:
        if spec.group_id not in known_groups:
            print(
                f"[artifacts] skip {spec.path}: unknown groupId '{spec.group_id}'"
            )
            continue
        if spec.artifact_type not in ArtifactType:
            raise ValueError(
                f"Unsupported artifact type '{spec.artifact_type}' in {spec.path}"
            )
        kept.append(spec)
    return kept
