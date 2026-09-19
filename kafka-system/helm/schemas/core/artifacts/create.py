#!/usr/bin/env python3
"""POST artifacts (empty or with firstVersion)."""

from __future__ import annotations

import json
from typing import Any

from core.common import content_payload, path_seg, post_json
from core.references import references_payload

from .artifact_types import ArtifactType, apicurio_artifact_type


def create_artifact(
    base: str,
    group_id: str,
    artifact_id: str,
    content: str | dict[str, Any] | None = None,
    *,
    artifact_type: str | ArtifactType = ArtifactType.AVRO,
    version: str = "1",
    name: str | None = None,
    description: str | None = None,
    references: list[dict[str, Any]] | None = None,
) -> bool:
    """POST /groups/{groupId}/artifacts.

    Omit content to create an empty artifact (no firstVersion).
    409 = already exists.
    """
    body: dict[str, Any] = {
        "artifactId": artifact_id,
        "artifactType": apicurio_artifact_type(artifact_type),
        "name": name or artifact_id,
    }
    if description:
        body["description"] = description
    if content is not None:
        if isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False)
        payload = content_payload(content)
        refs = references_payload(references)
        if refs:
            payload["references"] = refs
        body["firstVersion"] = {
            "version": version,
            "content": payload,
        }
    return post_json(f"{base}/groups/{path_seg(group_id)}/artifacts", body) in (200, 204)


def ensure_empty_artifact(
    base: str,
    group_id: str,
    artifact_id: str,
    *,
    existing_artifacts: set[str],
    artifact_type: str | ArtifactType = ArtifactType.AVRO,
    name: str | None = None,
    description: str | None = None,
) -> str:
    """Create an empty artifact if missing. Returns created | exists."""
    if artifact_id in existing_artifacts:
        return "exists"
    create_artifact(
        base,
        group_id,
        artifact_id,
        content=None,
        artifact_type=artifact_type,
        name=name,
        description=description,
    )
    existing_artifacts.add(artifact_id)
    return "created"
