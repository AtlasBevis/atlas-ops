#!/usr/bin/env python3
"""Plan version jobs: CDC Avro/Kafka Connect, heartbeat, JSON Schema log."""

from __future__ import annotations

from typing import Any

from core.bootstrap.constants import BOOTSTRAP_VERSION
from core.bootstrap.db import connector_source_artifact_id
from core.bootstrap.schemas import heartbeat_key_schema, heartbeat_value_schema

from .avro_names import avro_namespace
from .connect_schemas import (
    connect_envelope_schema,
    connect_heartbeat_key_schema,
    connect_heartbeat_value_schema,
    connect_key_schema,
)
from .models import Version, VersionState
from .parse import load_fields, load_json_schema
from .schemas import envelope_references, envelope_schema, key_schema, value_record_schema


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
    """Value records, then keys, then envelopes (envelope references .Value)."""
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
                "state": ver.state,
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
                # Envelope has no dedicated YAML state; it tracks the Value's.
                "state": ver.state,
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
                "state": ver.state,
            }
        )

    return value_jobs, key_jobs, envelope_jobs


def plan_heartbeat_versions(
    *,
    group_id: str,
    topic: str,
    connector: str,
    artifact_type: str = "AVRO",
    version: str = BOOTSTRAP_VERSION,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Debezium heartbeat: `{topic}-key` = ServerNameKey, `{topic}-value` = Heartbeat."""
    del group_id, connector
    is_connect = artifact_type == "KCONNECT"
    key_id = f"{topic}-key"
    value_id = f"{topic}-value"
    value_jobs = [
        {
            "artifact_id": value_id,
            "version": version,
            "content": (
                connect_heartbeat_value_schema()
                if is_connect
                else heartbeat_value_schema()
            ),
            "description": f"Debezium Heartbeat Value for {topic}",
            "references": None,
            "state": VersionState.ENABLED.value,
        }
    ]
    key_jobs = [
        {
            "artifact_id": key_id,
            "version": version,
            "content": (
                connect_heartbeat_key_schema()
                if is_connect
                else heartbeat_key_schema()
            ),
            "description": f"Debezium Heartbeat Key for {topic}",
            "references": None,
            "state": VersionState.ENABLED.value,
        }
    ]
    return value_jobs, key_jobs, []


def plan_connect_versions(
    *,
    topic: str,
    connector: str,
    key_versions: tuple[Version, ...],
    value_versions: tuple[Version, ...],
    key_description: str | None = None,
    value_description: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Debezium ExtJsonConverter: inline KCONNECT key and envelope schemas."""
    ns = avro_namespace(topic)
    value_jobs: list[dict[str, Any]] = []
    key_jobs: list[dict[str, Any]] = []

    for ver in value_versions:
        fields, _ = load_fields(ver.content_path, "value", connector)
        value_jobs.append(
            {
                "artifact_id": f"{topic}-value",
                "version": ver.version,
                "content": connect_envelope_schema(ns, fields, connector),
                "description": ver.description or value_description,
                "references": None,
                "state": ver.state,
            }
        )

    for ver in key_versions:
        fields, _ = load_fields(ver.content_path, "key", connector)
        key_jobs.append(
            {
                "artifact_id": f"{topic}-key",
                "version": ver.version,
                "content": connect_key_schema(ns, fields),
                "description": ver.description or key_description,
                "references": None,
                "state": ver.state,
            }
        )

    return value_jobs, key_jobs, []


def plan_log_versions(
    *,
    topic: str,
    key_versions: tuple[Version, ...],
    value_versions: tuple[Version, ...],
    key_description: str | None = None,
    value_description: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """JSON Schema log events: `{topic}-key` (optional) + `{topic}-value`."""
    value_jobs: list[dict[str, Any]] = []
    key_jobs: list[dict[str, Any]] = []
    for ver in value_versions:
        value_jobs.append(
            {
                "artifact_id": f"{topic}-value",
                "version": ver.version,
                "content": load_json_schema(ver.content_path),
                "description": ver.description or value_description,
                "references": None,
                "state": ver.state,
            }
        )
    for ver in key_versions:
        key_jobs.append(
            {
                "artifact_id": f"{topic}-key",
                "version": ver.version,
                "content": load_json_schema(ver.content_path),
                "description": ver.description or key_description,
                "references": None,
                "state": ver.state,
            }
        )
    return value_jobs, key_jobs, []
