#!/usr/bin/env python3
"""Artifact versions: model + parse + list/create API."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bootstrap import (
    BOOTSTRAP_VERSION,
    DEBEZIUM_GROUP,
    connector_source_artifact_id,
    heartbeat_key_schema,
    heartbeat_value_schema,
)
from common import content_payload, get_json, load_yaml, path_seg, post_json, require
from references import ArtifactReference, merge_references, parse_references, references_payload

from .mapping import map_column

VERSION_STATES = frozenset({"ENABLED", "DISABLED", "DEPRECATED", "DRAFT"})

# Avro Names — https://avro.apache.org/docs/++version++/specification/#names
# name: start [A-Za-z_], then only [A-Za-z0-9_]  →  [A-Za-z_][A-Za-z0-9_]*
# namespace: empty | name ('.' name)*
AVRO_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
AVRO_NAMESPACE_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*)?$"
)
# Characters illegal inside a name segment (hyphen, $, space, …)
_AVRO_ILLEGAL_IN_NAME = re.compile(r"[^A-Za-z0-9_]+")


@dataclass(frozen=True, slots=True)
class Version:
    """One artifact version: content file + optional outbound references."""

    version: str
    content_path: Path
    state: str = "ENABLED"
    description: str | None = None
    references: tuple[ArtifactReference, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError("version must be a non-empty string")

        if self.state not in VERSION_STATES:
            allowed = ", ".join(VERSION_STATES)
            raise ValueError(
                f"Invalid version state '{self.state}'. Allowed: {allowed}"
            )

        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("version description must be a string or omitted")

        if not isinstance(self.content_path, Path):
            raise ValueError("content_path must be a Path")


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


def avro_name_segment(part: str) -> str:
    """Sanitize one dot-separated segment to a legal Avro name.

    Spec: start with ``[A-Za-z_]``, then only ``[A-Za-z0-9_]``.
    Illegal runs (``-``, ``$``, space, …) become ``_``; leading digit → prefix ``_``.
    """
    cleaned = _AVRO_ILLEGAL_IN_NAME.sub("_", part)
    if not cleaned:
        cleaned = "_"
    if cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    if not AVRO_NAME_RE.fullmatch(cleaned):
        raise ValueError(f"Cannot form Avro name from segment {part!r} → {cleaned!r}")
    return cleaned


def avro_namespace(topic: str) -> str:
    """Derive a legal Avro namespace from a Kafka topic / topicPrefix path.

    Spec (Names): namespace = empty | name ('.' name)* where each name matches
    ``[A-Za-z_][A-Za-z0-9_]*``.

    https://avro.apache.org/docs/++version++/specification/#names

    Kafka topics may contain ``-`` (e.g. ``card-bo``); those characters are
    illegal in Avro and are replaced via :func:`avro_name_segment`.
    """
    text = topic.strip().strip(".")
    if not text:
        return ""
    segments = [avro_name_segment(p) for p in text.split(".") if p != ""]
    ns = ".".join(segments)
    if not AVRO_NAMESPACE_RE.fullmatch(ns):
        raise ValueError(
            f"Invalid Avro namespace derived from topic {topic!r}: {ns!r}"
        )
    return ns


def key_schema(ns: str, fields: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "record",
        "name": "Key",
        "namespace": ns,
        "fields": fields,
        "connect.name": f"{ns}.Key",
    }


def value_record_schema(ns: str, fields: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "record",
        "name": "Value",
        "namespace": ns,
        "fields": fields,
        "connect.name": f"{ns}.Value",
    }


def envelope_schema(ns: str, source_type: str, value_fqn: str) -> dict[str, Any]:
    return {
        "type": "record",
        "name": "Envelope",
        "namespace": ns,
        "fields": [
            {"name": "before", "type": ["null", value_fqn], "default": None},
            {"name": "after", "type": ["null", value_fqn], "default": None},
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


def bootstrap_reference(artifact_id: str) -> dict[str, str]:
    return {
        "name": artifact_id,
        "groupId": DEBEZIUM_GROUP,
        "artifactId": artifact_id,
        "version": BOOTSTRAP_VERSION,
    }


def debezium_shared_references(connector: str) -> list[dict[str, str]]:
    return [
        bootstrap_reference(connector_source_artifact_id(connector)),
        bootstrap_reference("event.block"),
    ]


def envelope_references(
    group_id: str,
    value_ns: str,
    value_version: str,
    connector: str,
    extra: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    value_id = f"{value_ns}.Value"
    return [
        {
            "name": value_id,
            "groupId": group_id,
            "artifactId": value_id,
            "version": value_version,
        },
        *debezium_shared_references(connector),
        *(extra or []),
    ]


def plan_versions(
    *,
    group_id: str,
    topic: str,
    connector: str,
    key_versions: tuple[Version, ...],
    value_versions: tuple[Version, ...],
    key_description: str | None = None,
    value_description: str | None = None,
    envelope_description: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Value records, then keys, then envelopes (envelope references .Value).

    Kafka ``topic`` may contain ``-`` (legal). Avro namespace / ``.Value``
    artifactId use ``avro_namespace(topic)`` (illegal chars → ``_``).
    """
    source_type = connector_source_artifact_id(connector)
    ns = avro_namespace(topic)
    key_id = f"{topic}-key"
    record_id = f"{ns}.Value"
    envelope_id = f"{topic}-value"
    value_fqn = f"{ns}.Value"

    value_jobs: list[dict[str, Any]] = []
    key_jobs: list[dict[str, Any]] = []
    envelope_jobs: list[dict[str, Any]] = []

    for ver in value_versions:
        fields, field_refs = load_fields(ver.content_path, "value", connector)
        value_jobs.append(
            {
                "artifact_id": record_id,
                "version": ver.version,
                "content": value_record_schema(ns, fields),
                "description": ver.description or value_description,
                "references": field_refs or None,
            }
        )
        envelope_jobs.append(
            {
                "artifact_id": envelope_id,
                "version": ver.version,
                "content": envelope_schema(ns, source_type, value_fqn),
                "description": ver.description or envelope_description,
                "references": envelope_references(
                    group_id,
                    ns,
                    ver.version,
                    connector,
                ),
            }
        )

    for ver in key_versions:
        fields, field_refs = load_fields(ver.content_path, "key", connector)
        key_jobs.append(
            {
                "artifact_id": key_id,
                "version": ver.version,
                "content": key_schema(ns, fields),
                "description": ver.description or key_description,
                "references": field_refs or None,
            }
        )

    return value_jobs, key_jobs, envelope_jobs


def plan_heartbeat_versions(
    *,
    group_id: str,
    topic: str,
    connector: str,
    version: str = BOOTSTRAP_VERSION,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Debezium heartbeat: `{topic}-key` = ServerNameKey, `{topic}-value` = Heartbeat.

    No `.Value` and no Envelope — the message value is Heartbeat (`ts_ms`).
    """
    del group_id, connector
    key_id = f"{topic}-key"
    value_id = f"{topic}-value"
    value_jobs = [
        {
            "artifact_id": value_id,
            "version": version,
            "content": heartbeat_value_schema(),
            "description": f"Debezium Heartbeat Value for {topic}",
            "references": None,
        }
    ]
    key_jobs = [
        {
            "artifact_id": key_id,
            "version": version,
            "content": heartbeat_key_schema(),
            "description": f"Debezium Heartbeat Key for {topic}",
            "references": None,
        }
    ]
    return value_jobs, key_jobs, []


def list_versions(base: str, group_id: str, artifact_id: str) -> set[str]:
    """GET /groups/{groupId}/artifacts/{artifactId}/versions."""
    ids: set[str] = set()
    offset = 0
    limit = 100
    while True:
        url = (
            f"{base}/groups/{path_seg(group_id)}/artifacts/{path_seg(artifact_id)}/versions"
            f"?limit={limit}&offset={offset}"
        )
        data = get_json(url, allow_404=True)
        rows = data.get("versions") if isinstance(data, dict) else data
        if not rows:
            break
        for row in rows:
            if isinstance(row, dict):
                ver = row.get("version") or row.get("versionId")
            else:
                ver = row
            if ver:
                ids.add(str(ver))
        if len(rows) < limit:
            break
        offset += limit
    return ids


def create_version(
    base: str,
    group_id: str,
    artifact_id: str,
    content: str | dict[str, Any],
    *,
    version: str,
    description: str | None = None,
    references: list[dict[str, Any]] | tuple[ArtifactReference, ...] | None = None,
) -> bool:
    """POST /groups/{groupId}/artifacts/{artifactId}/versions. 409 = already exists."""
    if isinstance(content, dict):
        content = json.dumps(content, ensure_ascii=False)
    payload = content_payload(content)
    refs = references_payload(references)
    if refs:
        payload["references"] = refs
    body: dict[str, Any] = {
        "version": version,
        "content": payload,
    }
    if description:
        body["description"] = description
    url = (
        f"{base}/groups/{path_seg(group_id)}/artifacts/{path_seg(artifact_id)}/versions"
    )
    return post_json(url, body) in (200, 204)


def ensure_version(
    base: str,
    group_id: str,
    artifact_id: str,
    content: str | dict[str, Any],
    *,
    version: str,
    description: str | None = None,
    references: list[dict[str, Any]] | tuple[ArtifactReference, ...] | None = None,
) -> str:
    """Create a version if missing. Returns version | exists."""
    versions = list_versions(base, group_id, artifact_id)
    if version in versions:
        return "exists"
    create_version(
        base,
        group_id,
        artifact_id,
        content,
        version=version,
        description=description,
        references=references,
    )
    return "version"


def sync_versions(
    base: str,
    group_id: str,
    jobs: list[dict[str, Any]],
) -> tuple[int, int]:
    """Create missing versions. Returns (created, skipped)."""
    created = 0
    skipped = 0
    for job in jobs:
        result = ensure_version(
            base,
            group_id,
            job["artifact_id"],
            job["content"],
            version=job["version"],
            description=job["description"],
            references=job["references"],
        )
        if result == "version":
            created += 1
        else:
            skipped += 1
    return created, skipped
