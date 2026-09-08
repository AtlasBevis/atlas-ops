#!/usr/bin/env python3
"""Artifact version + Apicurio content references."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from common import require

# Apicurio version states commonly used by the registry.
VERSION_STATES = frozenset({"ENABLED", "DISABLED", "DEPRECATED", "DRAFT"})

# Same pattern as GroupId / ArtifactId in Apicurio Registry REST API.
_ID_LEN = range(1, 513)


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    """Pointer from version content → another artifact version.

    Maps to Apicurio CreateContent.references[]:
      { name, groupId, artifactId, version }
    """

    name: str
    group_id: str
    artifact_id: str
    version: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("name", self.name),
            ("groupId", self.group_id),
            ("artifactId", self.artifact_id),
            ("version", self.version),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"reference.{field_name} must be a non-empty string")
            if field_name in ("groupId", "artifactId") and len(value) not in _ID_LEN:
                raise ValueError(
                    f"reference.{field_name} '{value}' must be 1–512 characters"
                )

    @property
    def coord(self) -> tuple[str, str, str]:
        return (self.group_id, self.artifact_id, self.version)


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
            allowed = ", ".join(sorted(VERSION_STATES))
            raise ValueError(
                f"Invalid version state '{self.state}'. Allowed: {allowed}"
            )
        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("version description must be a string or omitted")
        if not isinstance(self.content_path, Path):
            raise ValueError("content_path must be a Path")


def parse_references(
    raw: object,
    *,
    path: Path,
    loc: str,
) -> tuple[ArtifactReference, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ValueError(f"{loc}.references must be a list in {path}")

    refs: list[ArtifactReference] = []
    seen_names: set[str] = set()
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise ValueError(f"{loc}.references[{i}] must be an object in {path}")
        ref = ArtifactReference(
            name=require(entry, "name", path),
            group_id=require(entry, "groupId", path),
            artifact_id=require(entry, "artifactId", path),
            version=str(require(entry, "version", path)),
        )
        if ref.name in seen_names:
            raise ValueError(
                f"{loc}.references duplicate name '{ref.name}' in {path}"
            )
        seen_names.add(ref.name)
        refs.append(ref)
    return tuple(refs)


def parse_version(entry: dict, *, path: Path, loc: str) -> Version:
    version = str(require(entry, "version", path))
    content = require(entry, "content", path)
    if not isinstance(content, str) or not content.strip():
        raise ValueError(f"{loc}.content must be a non-empty relative path in {path}")

    content_path = (path.parent / content).resolve()
    if not content_path.is_file():
        raise ValueError(f"{loc}.content file not found: {content_path}")

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
