#!/usr/bin/env python3
"""GET groups."""

from __future__ import annotations

from core.common import get_json


def list_groups(base: str) -> set[str]:
    """GET /groups (paged list of groupIds)."""
    data = get_json(f"{base}/groups")
    return {g["groupId"] for g in data.get("groups") or [] if g.get("groupId")}
