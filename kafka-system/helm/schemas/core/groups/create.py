#!/usr/bin/env python3
"""POST groups."""

from __future__ import annotations

from core.common import post_json


def create_group(base: str, group_id: str, description: str | None = None) -> bool:
    """POST /groups"""
    body: dict = {"groupId": group_id}
    if description:
        body["description"] = description
    return post_json(f"{base}/groups", body) == 200
