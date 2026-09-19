#!/usr/bin/env python3
"""Apicurio artifactType + YAML source.type / source.format."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any

class ArtifactType(str, Enum):
    """Apicurio `artifactType`"""

    AVRO = "AVRO"
    JSON = "JSON"
    KCONNECT = "KCONNECT"


class SourceType(str, Enum):
    """YAML `source.type`"""

    DEBEZIUM = "debezium"
    LOG = "log"


FORMAT_AVRO = "avro"
FORMAT_JSON = "json"

# source.format → source.type → Apicurio artifactType.
# Omitted source.format is always JSON (see parse_artifact_type).
_ARTIFACT_TYPE_BY_FORMAT: dict[str, dict[SourceType, ArtifactType]] = {
    FORMAT_AVRO: {
        SourceType.DEBEZIUM: ArtifactType.AVRO,
    },
    FORMAT_JSON: {
        SourceType.DEBEZIUM: ArtifactType.KCONNECT,
        SourceType.LOG: ArtifactType.JSON,
    },
}


def parse_source_type(raw: object, path: Path) -> SourceType:
    try:
        return SourceType(raw)
    except ValueError:
        allowed = ", ".join(sorted(t.value for t in SourceType))
        raise ValueError(
            f"'source.type' must be one of: {allowed} in {path}"
        ) from None


def parse_artifact_type(
    source: dict[str, Any],
    *,
    source_type: SourceType,
    path: Path,
) -> ArtifactType:
    """Resolve Apicurio artifactType; omitted `source.format` defaults to JSON."""
    raw = source.get("format", FORMAT_JSON)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"'source.format' must be a non-empty string in {path}")

    format_name = raw.strip().lower()
    artifact_types = _ARTIFACT_TYPE_BY_FORMAT.get(format_name)
    if artifact_types is None:
        allowed = ", ".join(sorted(_ARTIFACT_TYPE_BY_FORMAT))
        raise ValueError(
            f"Unsupported source.format '{raw}' in {path}. Allowed: {allowed}"
        )

    artifact_type = artifact_types.get(source_type)
    if artifact_type is None:
        allowed = ", ".join(sorted(s.value for s in artifact_types))
        raise ValueError(
            f"source.format '{format_name}' does not support source.type "
            f"'{source_type.value}' in {path}. Allowed: {allowed}"
        )
    return artifact_type


def apicurio_artifact_type(value: ArtifactType | str) -> str:
    return value.value if isinstance(value, ArtifactType) else value
