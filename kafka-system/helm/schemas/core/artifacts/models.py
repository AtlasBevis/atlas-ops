#!/usr/bin/env python3
"""Table index models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.versions.models import Version

from .artifact_types import ArtifactType, SourceType


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
    source_type: SourceType
    artifact_type: ArtifactType
    connector: str
    heartbeat: bool
    heartbeat_prefix: str | None
    table: TableSpec


@dataclass(frozen=True, slots=True)
class EmptyArtifact:
    artifact_id: str
    name: str
    description: str | None
    artifact_type: ArtifactType
