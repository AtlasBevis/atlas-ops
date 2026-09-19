#!/usr/bin/env python3
"""POST artifact versions."""

from __future__ import annotations

import json
from typing import Any

from core.common import content_payload, path_seg, post_json
from core.references import ArtifactReference, references_payload

from .list import list_versions


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


def ensure_version(
    base: str,
    group_id: str,
    artifact_id: str,
    content: str | dict[str, Any],
    *,
    version: str,
    description: str | None = None,
    references: list[dict[str, Any]] | tuple[ArtifactReference, ...] | None = None,
) -> str:
    """Create a version if missing. Returns version | exists."""
    versions = list_versions(base, group_id, artifact_id)
    if version in versions:
        return "exists"
    create_version(
        base,
        group_id,
        artifact_id,
        content,
        version=version,
        description=description,
        references=references,
    )
    return "version"
