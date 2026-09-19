#!/usr/bin/env python3
"""GET version references."""

from __future__ import annotations

from typing import Any

from core.common import get_json, path_seg


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
