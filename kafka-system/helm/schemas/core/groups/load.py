#!/usr/bin/env python3
"""Load groups from domain/index.yaml."""

from __future__ import annotations

from core.common import GROUPS_FILE, load_yaml, require

from .models import Group


def load_groups() -> list[Group]:
    if not GROUPS_FILE.is_file():
        raise FileNotFoundError(f"Groups file not found: {GROUPS_FILE}")

    data = load_yaml(GROUPS_FILE)
    rows = require(data, "groups", GROUPS_FILE)
    if not isinstance(rows, list):
        raise ValueError(f"'groups' must be a list in {GROUPS_FILE}")

    groups: list[Group] = []
    seen: set[str] = set()
    for i, entry in enumerate(rows):
        if not isinstance(entry, dict):
            raise ValueError(f"groups[{i}] must be an object in {GROUPS_FILE}")

        group_id = require(entry, "groupId", GROUPS_FILE)
        description = entry.get("description")
        group = Group(
            group_id=group_id,
            description=description,
        )

        if group.group_id in seen:
            raise ValueError(
                f"Duplicate groupId '{group.group_id}' in {GROUPS_FILE}"
            )
        seen.add(group.group_id)
        groups.append(group)

    return groups
