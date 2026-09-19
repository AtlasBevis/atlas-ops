#!/usr/bin/env python3
"""Parse / merge reference payloads."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from core.common import require

from .models import ArtifactReference


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
