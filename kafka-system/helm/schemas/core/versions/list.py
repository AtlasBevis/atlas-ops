#!/usr/bin/env python3
"""GET artifact versions."""

from __future__ import annotations

from core.common import get_json, path_seg


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
