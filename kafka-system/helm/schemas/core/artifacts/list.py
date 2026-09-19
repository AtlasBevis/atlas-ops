#!/usr/bin/env python3
"""GET artifacts in a group."""

from __future__ import annotations

from core.common import get_json, path_seg


def list_artifacts(base: str, group_id: str) -> set[str]:
    """List artifact IDs in a group: GET /groups/{groupId}/artifacts"""
    ids: set[str] = set()
    offset = 0
    limit = 100
    while True:
        url = (
            f"{base}/groups/{path_seg(group_id)}/artifacts"
            f"?limit={limit}&offset={offset}"
        )
        data = get_json(url, allow_404=True)
        rows = data.get("artifacts") if isinstance(data, dict) else data
        if not rows:
            break
        for row in rows:
            aid = row.get("artifactId") if isinstance(row, dict) else None
            if aid:
                ids.add(aid)
        if len(rows) < limit:
            break
        offset += limit
    return ids
