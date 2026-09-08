#!/usr/bin/env python3
"""Artifact versions: model + parse + list/create API."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from common import content_payload, get_json, path_seg, post_json, require
from references import ArtifactReference, parse_references, references_payload

VERSION_STATES = frozenset({"ENABLED", "DISABLED", "DEPRECATED", "DRAFT"})


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


def list_versions(base: str, group_id: str, artifact_id: str) -> set[str]:
    """GET /groups/{groupId}/artifacts/{artifactId}/versions."""
    
    ids: set[str] = set()
    offset = 0
    limit = 100
    while True:
        url = (
            f"{base}/groups/{path_seg(group_id)}/artifacts/{path_seg(artifact_id)}/versions"
            f"?limit={limit}&offset={offset}"
        )
        data = get_json(url, allow_404=True)
        rows = data.get("versions") if isinstance(data, dict) else data
        if not rows:
            break
        for row in rows:
            if isinstance(row, dict):
                ver = row.get("version") or row.get("versionId")
            else:
                ver = row
            if ver:
                ids.add(str(ver))
        if len(rows) < limit:
            break
        offset += limit
    return ids


def create_version(
    base: str,
    group_id: str,
    artifact_id: str,
    content: str | dict[str, Any],
    *,
    version: str,
    description: str | None = None,
    references: list[dict[str, Any]] | tuple[ArtifactReference, ...] | None = None,
) -> bool:
    """POST /groups/{groupId}/artifacts/{artifactId}/versions. 409 = already exists."""
    if isinstance(content, dict):
        content = json.dumps(content, ensure_ascii=False)
    payload = content_payload(content)
    refs = references_payload(references)
    if refs:
        payload["references"] = refs
    body: dict[str, Any] = {
        "version": version,
        "content": payload,
    }
    if description:
        body["description"] = description
    url = (
        f"{base}/groups/{path_seg(group_id)}/artifacts/{path_seg(artifact_id)}/versions"
    )
    return post_json(url, body) in (200, 204)
