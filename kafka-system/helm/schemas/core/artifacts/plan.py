#!/usr/bin/env python3
"""Plan empty artifacts and version jobs from a table index."""

from __future__ import annotations

from typing import Any

from core.versions.avro_names import avro_namespace
from core.versions.plan import (
    plan_connect_versions,
    plan_heartbeat_versions,
    plan_log_versions,
    plan_versions,
)

from .artifact_types import ArtifactType, SourceType
from .models import EmptyArtifact, TableIndex


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
    Avro namespace form (``-`` → ``_``) so the artifactId matches connect.name.
    """
    ns = avro_namespace(topic)
    return f"{topic}-key", f"{ns}.Value", f"{topic}-value"


def plan_heartbeat_empty_artifacts(
    topic: str,
    artifact_type: ArtifactType,
) -> list[EmptyArtifact]:
    key_id = f"{topic}-key"
    value_id = f"{topic}-value"
    return [
        EmptyArtifact(
            key_id, key_id, f"Debezium Heartbeat Key for {topic}", artifact_type
        ),
        EmptyArtifact(
            value_id, value_id, f"Debezium Heartbeat Value for {topic}", artifact_type
        ),
    ]


def plan_empty_artifacts(spec: TableIndex) -> list[EmptyArtifact]:
    table = spec.table
    topic = kafka_topic(spec)
    if spec.artifact_type is ArtifactType.JSON:
        items: list[EmptyArtifact] = []
        if table.key_versions:
            items.append(
                EmptyArtifact(
                    f"{topic}-key",
                    f"{topic}-key",
                    table.key_description or f"JSON Key for {topic}",
                    ArtifactType.JSON,
                )
            )
        items.append(
            EmptyArtifact(
                f"{topic}-value",
                f"{topic}-value",
                table.value_description or table.description or f"JSON Value for {topic}",
                ArtifactType.JSON,
            )
        )
        return items

    if spec.artifact_type is ArtifactType.KCONNECT:
        return [
            EmptyArtifact(
                f"{topic}-key",
                f"{topic}-key",
                table.key_description or f"CDC Key for {topic}",
                ArtifactType.KCONNECT,
            ),
            EmptyArtifact(
                f"{topic}-value",
                f"{topic}-value",
                table.description or f"CDC Envelope for {topic}",
                ArtifactType.KCONNECT,
            ),
        ]

    if spec.artifact_type is ArtifactType.AVRO:
        key_id, record_id, envelope_id = debezium_artifact_ids(topic)
        return [
            EmptyArtifact(
                key_id,
                key_id,
                table.key_description or f"CDC Key for {topic}",
                ArtifactType.AVRO,
            ),
            EmptyArtifact(
                record_id,
                record_id,
                table.value_description or f"CDC Value for {topic}",
                ArtifactType.AVRO,
            ),
            EmptyArtifact(
                envelope_id,
                envelope_id,
                table.description or f"CDC Envelope for {topic}",
                ArtifactType.AVRO,
            ),
        ]

    raise ValueError(
        f"No empty-artifact planner for type {spec.artifact_type.value} in {spec.path}"
    )


def plan_version_jobs(
    spec: TableIndex,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    topic = kafka_topic(spec)
    table = spec.table
    if (
        spec.source_type is SourceType.LOG
        and spec.artifact_type is ArtifactType.JSON
    ):
        return plan_log_versions(
            topic=topic,
            key_versions=table.key_versions,
            value_versions=table.value_versions,
            key_description=table.key_description,
            value_description=table.value_description,
        )
    if (
        spec.source_type is SourceType.DEBEZIUM
        and spec.artifact_type is ArtifactType.AVRO
    ):
        return plan_versions(
            group_id=spec.group_id,
            topic=topic,
            connector=spec.connector,
            key_versions=table.key_versions,
            value_versions=table.value_versions,
            key_description=table.key_description,
            value_description=table.value_description,
            envelope_description=table.description,
        )
    if (
        spec.source_type is SourceType.DEBEZIUM
        and spec.artifact_type is ArtifactType.KCONNECT
    ):
        return plan_connect_versions(
            topic=topic,
            connector=spec.connector,
            key_versions=table.key_versions,
            value_versions=table.value_versions,
            key_description=table.key_description,
            value_description=table.description or table.value_description,
        )
    raise ValueError(
        f"No version planner for type {spec.artifact_type.value} in {spec.path}"
    )
