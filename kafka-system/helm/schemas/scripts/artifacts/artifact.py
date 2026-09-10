#!/usr/bin/env python3
"""
Manifest artifact definitions
https://www.apicur.io/registry/docs/apicurio-registry/3.0.x/assets-attachments/registry-rest-api.htm#tag/Artifacts
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common import GROUPS_ROOT, content_payload, get_json, load_yaml, path_seg, post_json, require
from references import references_payload
from versions import (
    Version,
    avro_namespace,
    parse_versions,
    plan_heartbeat_versions,
    plan_versions,
    sync_versions,
)

SOURCE_DEBEZIUM = "debezium"
SOURCE_LOG = "log"
SOURCE_TYPES = frozenset({SOURCE_DEBEZIUM, SOURCE_LOG})


@dataclass(frozen=True, slots=True)
class TableSpec:
    name: str
    description: str | None
    key_description: str | None
    value_description: str | None
    key_versions: tuple[Version, ...]
    value_versions: tuple[Version, ...]


@dataclass(frozen=True, slots=True)
class TableIndex:
    path: Path
    group_id: str
    db_schema: str
    topic_prefix: str
    source_type: str
    connector: str
    heartbeat: bool
    heartbeat_prefix: str | None
    table: TableSpec


def list_artifacts(base: str, group_id: str) -> set[str]:
    """List artifact IDs in a group: GET /groups/{groupId}/artifacts"""
    ids: set[str] = set()
    offset = 0
    limit = 100
    while True:
        url = (
            f"{base}/groups/{path_seg(group_id)}/artifacts"
            f"?limit={limit}&offset={offset}"
        )
        data = get_json(url, allow_404=True)
        rows = data.get("artifacts") if isinstance(data, dict) else data
        if not rows:
            break
        for row in rows:
            aid = row.get("artifactId") if isinstance(row, dict) else None
            if aid:
                ids.add(aid)
        if len(rows) < limit:
            break
        offset += limit
    return ids


def create_artifact(
    base: str,
    group_id: str,
    artifact_id: str,
    content: str | dict[str, Any] | None = None,
    *,
    artifact_type: str = "AVRO",
    version: str = "1",
    name: str | None = None,
    description: str | None = None,
    references: list[dict[str, Any]] | None = None,
) -> bool:
    """POST /groups/{groupId}/artifacts.

    Omit content to create an empty artifact (no firstVersion).
    409 = already exists.
    """
    body: dict[str, Any] = {
        "artifactId": artifact_id,
        "artifactType": artifact_type,
        "name": name or artifact_id,
    }
    if description:
        body["description"] = description
    if content is not None:
        if isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False)
        payload = content_payload(content)
        refs = references_payload(references)
        if refs:
            payload["references"] = refs
        body["firstVersion"] = {
            "version": version,
            "content": payload,
        }
    return post_json(f"{base}/groups/{path_seg(group_id)}/artifacts", body) in (200, 204)


def ensure_empty_artifact(
    base: str,
    group_id: str,
    artifact_id: str,
    *,
    existing_artifacts: set[str],
    artifact_type: str = "AVRO",
    name: str | None = None,
    description: str | None = None,
) -> str:
    """Create an empty artifact if missing. Returns created | exists."""
    if artifact_id in existing_artifacts:
        return "exists"
    create_artifact(
        base,
        group_id,
        artifact_id,
        content=None,
        artifact_type=artifact_type,
        name=name,
        description=description,
    )
    existing_artifacts.add(artifact_id)
    return "created"


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
) -> tuple[str | None, tuple[Version, ...]]:
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
    
    source_type = source.get("type")
    if source_type not in SOURCE_TYPES:
        allowed = ", ".join(sorted(SOURCE_TYPES))
        raise ValueError(
            f"'source.type' must be one of: {allowed} in {spec_path}"
        )
    
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

    key_desc, key_versions = _parse_side(
        require(entry, "key", spec_path),
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
        source_type=str(source_type),
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
        if spec.source_type not in SOURCE_TYPES:
            allowed = ", ".join(sorted(SOURCE_TYPES))
            raise ValueError(
                f"Unsupported source.type '{spec.source_type}' in {spec.path}. "
                f"Allowed: {allowed}"
            )
        kept.append(spec)
    return kept


def kafka_topic(spec: TableIndex) -> str:
    return f"{spec.topic_prefix}.{spec.db_schema}.{spec.table.name}"


def heartbeat_topic(spec: TableIndex) -> str:
    """Debezium: ${topic.heartbeat.prefix}.${topic.prefix}."""
    prefix = (spec.heartbeat_prefix or "").strip().rstrip(".")
    topic_prefix = spec.topic_prefix.strip().strip(".")
    return f"{prefix}.{topic_prefix}"


def debezium_artifact_ids(topic: str) -> tuple[str, str, str]:
    """Return (key, Value, envelope) artifactIds for a Kafka topic.

    ``-key`` / ``-value`` keep the topic (hyphens OK). ``.Value`` uses the
    Avro namespace form (illegal chars → ``_``) so artifactId matches connect.name.
    """
    ns = avro_namespace(topic)
    return f"{topic}-key", f"{ns}.Value", f"{topic}-value"


def plan_heartbeat_empty_artifacts(topic: str) -> list[tuple[str, str, str | None]]:
    key_id = f"{topic}-key"
    value_id = f"{topic}-value"
    return [
        (key_id, key_id, f"Debezium Heartbeat Key for {topic}"),
        (value_id, value_id, f"Debezium Heartbeat Value for {topic}"),
    ]


def plan_empty_artifacts(spec: TableIndex) -> list[tuple[str, str, str | None]]:
    table = spec.table
    topic = kafka_topic(spec)
    key_id, record_id, envelope_id = debezium_artifact_ids(topic)
    return [
        (key_id, key_id, table.key_description or f"CDC Key for {topic}"),
        (record_id, record_id, table.value_description or f"CDC Value for {topic}"),
        (envelope_id, envelope_id, table.description or f"CDC Envelope for {topic}"),
    ]


def sync_artifacts(base: str, groups: set[str]) -> None:
    """Create empty artifacts per group, then versions for those artifactIds."""
    indexes = filter_table_indexes(load_table_indexes(), groups)

    by_group: dict[str, list[TableIndex]] = {}
    for spec in indexes:
        by_group.setdefault(spec.group_id, []).append(spec)

    created = 0
    versioned = 0
    skipped = 0

    for group_id in sorted(by_group):
        existing = list_artifacts(base, group_id)
        empties: list[tuple[str, str, str | None]] = []
        value_jobs: list[dict[str, Any]] = []
        key_jobs: list[dict[str, Any]] = []
        envelope_jobs: list[dict[str, Any]] = []
        heartbeat_seen: set[str] = set()

        for spec in by_group[group_id]:
            if (
                spec.source_type == SOURCE_DEBEZIUM
                and spec.heartbeat
                and spec.heartbeat_prefix
            ):
                hb_topic = heartbeat_topic(spec)
                if hb_topic not in heartbeat_seen:
                    heartbeat_seen.add(hb_topic)
                    empties.extend(plan_heartbeat_empty_artifacts(hb_topic))
                    values, keys, envelopes = plan_heartbeat_versions(
                        group_id=spec.group_id,
                        topic=hb_topic,
                        connector=spec.connector,
                    )
                    value_jobs.extend(values)
                    key_jobs.extend(keys)
                    envelope_jobs.extend(envelopes)

            empties.extend(plan_empty_artifacts(spec))
            values, keys, envelopes = plan_versions(
                group_id=spec.group_id,
                topic=kafka_topic(spec),
                connector=spec.connector,
                key_versions=spec.table.key_versions,
                value_versions=spec.table.value_versions,
                key_description=spec.table.key_description,
                value_description=spec.table.value_description,
                envelope_description=spec.table.description,
            )
            value_jobs.extend(values)
            key_jobs.extend(keys)
            envelope_jobs.extend(envelopes)

        for artifact_id, name, description in empties:
            result = ensure_empty_artifact(
                base,
                group_id,
                artifact_id,
                existing_artifacts=existing,
                name=name,
                description=description,
            )
            if result == "created":
                created += 1
            else:
                skipped += 1

        added, missed = sync_versions(
            base,
            group_id,
            value_jobs + key_jobs + envelope_jobs,
        )
        versioned += added
        skipped += missed

    print(
        f"[artifacts] groups={len(by_group)} indexes={len(indexes)} "
        f"created={created} versions={versioned} skipped={skipped}"
    )
