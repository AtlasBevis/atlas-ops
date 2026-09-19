#!/usr/bin/env python3
"""Apicurio content reference model."""

from __future__ import annotations

from dataclasses import dataclass

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

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "groupId": self.group_id,
            "artifactId": self.artifact_id,
            "version": self.version,
        }
