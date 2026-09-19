#!/usr/bin/env python3
"""Create missing catalog groups."""

from __future__ import annotations

from .create import create_group
from .list import list_groups
from .load import load_groups


def sync_groups(base: str) -> set[str]:
    desired = load_groups()
    existing = list_groups(base)
    created = 0
    for g in desired:
        if g.group_id in existing:
            continue

        if create_group(base, g.group_id, g.description):
            created += 1

        existing.add(g.group_id)

    print(f"[groups] listed={len(existing)} created={created}")
    return existing
