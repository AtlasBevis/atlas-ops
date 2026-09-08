#!/usr/bin/env python3
"""Apicurio content references: model + parse + list API."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from common import get_json, path_seg, require

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


def references_payload(
    refs: Iterable[ArtifactReference | dict[str, Any]] | None,
) -> list[dict[str, str]] | None:
    if not refs:
        return None
    out: list[dict[str, str]] = []
    for ref in refs:
        if isinstance(ref, ArtifactReference):
            out.append(ref.as_dict())
        else:
            out.append(ref)
    return out


def merge_references(
    *groups: tuple[dict[str, str], ...] | list[dict[str, str]],
) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for refs in groups:
        for ref in refs:
            merged[ref["name"]] = ref
    return list(merged.values())


def list_references(
    base: str,
    group_id: str,
    artifact_id: str,
    version: str,
) -> list[dict[str, Any]]:
    """GET /groups/{groupId}/artifacts/{artifactId}/versions/{version}/references."""
    url = (
        f"{base}/groups/{path_seg(group_id)}/artifacts/{path_seg(artifact_id)}"
        f"/versions/{path_seg(version)}/references"
    )
    data = get_json(url, allow_404=True)
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        rows = data.get("references") or []
        return [row for row in rows if isinstance(row, dict)]
    return []
