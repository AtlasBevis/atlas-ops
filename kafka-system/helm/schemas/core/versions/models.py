#!/usr/bin/env python3
"""Artifact version model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from core.references.models import ArtifactReference


class VersionState(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    DEPRECATED = "DEPRECATED"
    DRAFT = "DRAFT"


@dataclass(frozen=True, slots=True)
class Version:
    """One artifact version: content file + optional outbound references."""

    version: str
    content_path: Path
    state: str = VersionState.ENABLED.value
    description: str | None = None
    references: tuple[ArtifactReference, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError("version must be a non-empty string")

        try:
            VersionState(self.state)
        except ValueError:
            allowed = ", ".join(s.value for s in VersionState)
            raise ValueError(
                f"Invalid version state '{self.state}'. Allowed: {allowed}"
            ) from None

        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("version description must be a string or omitted")

        if not isinstance(self.content_path, Path):
            raise ValueError("content_path must be a Path")
