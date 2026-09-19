#!/usr/bin/env python3
"""Create empty artifacts per group, then versions."""

from __future__ import annotations

from typing import Any

from core.versions.plan import plan_heartbeat_versions
from core.versions.sync import sync_versions

from .artifact_types import ArtifactType, SourceType
from .create import ensure_empty_artifact
from .list import list_artifacts
from .load import filter_table_indexes, load_table_indexes
from .models import EmptyArtifact, TableIndex
from .plan import (
    heartbeat_topic,
    plan_empty_artifacts,
    plan_heartbeat_empty_artifacts,
    plan_version_jobs,
)


def sync_artifacts(base: str, groups: set[str]) -> None:
    """Create empty artifacts per group, then versions for those artifactIds."""
    indexes = filter_table_indexes(load_table_indexes(), groups)

    by_group: dict[str, list[TableIndex]] = {}
    for spec in indexes:
        by_group.setdefault(spec.group_id, []).append(spec)

    created = 0
    versioned = 0
    skipped = 0
    state_changed = 0

    for group_id in sorted(by_group):
        existing = list_artifacts(base, group_id)
        empties: list[EmptyArtifact] = []
        value_jobs: list[dict[str, Any]] = []
        key_jobs: list[dict[str, Any]] = []
        envelope_jobs: list[dict[str, Any]] = []
        heartbeat_seen: dict[str, ArtifactType] = {}

        for spec in by_group[group_id]:
            if (
                spec.source_type is SourceType.DEBEZIUM
                and spec.artifact_type
                in {ArtifactType.AVRO, ArtifactType.KCONNECT}
                and spec.heartbeat
                and spec.heartbeat_prefix
            ):
                hb_topic = heartbeat_topic(spec)
                existing_type = heartbeat_seen.get(hb_topic)
                if existing_type is not None and existing_type is not spec.artifact_type:
                    raise ValueError(
                        f"Heartbeat topic '{hb_topic}' in group '{group_id}' "
                        f"cannot mix {existing_type.value} and "
                        f"{spec.artifact_type.value}"
                    )
                if existing_type is None:
                    heartbeat_seen[hb_topic] = spec.artifact_type
                    empties.extend(
                        plan_heartbeat_empty_artifacts(
                            hb_topic,
                            spec.artifact_type,
                        )
                    )
                    values, keys, envelopes = plan_heartbeat_versions(
                        group_id=spec.group_id,
                        topic=hb_topic,
                        connector=spec.connector,
                        artifact_type=spec.artifact_type.value,
                    )
                    value_jobs.extend(values)
                    key_jobs.extend(keys)
                    envelope_jobs.extend(envelopes)

            empties.extend(plan_empty_artifacts(spec))
            values, keys, envelopes = plan_version_jobs(spec)
            value_jobs.extend(values)
            key_jobs.extend(keys)
            envelope_jobs.extend(envelopes)

        for item in empties:
            result = ensure_empty_artifact(
                base,
                group_id,
                item.artifact_id,
                existing_artifacts=existing,
                artifact_type=item.artifact_type,
                name=item.name,
                description=item.description,
            )
            if result == "created":
                created += 1
            else:
                skipped += 1

        added, missed, changed = sync_versions(
            base,
            group_id,
            value_jobs + key_jobs + envelope_jobs,
        )
        versioned += added
        skipped += missed
        state_changed += changed

    print(
        f"[artifacts] groups={len(by_group)} indexes={len(indexes)} "
        f"created={created} versions={versioned} state_changed={state_changed} "
        f"skipped={skipped}"
    )
