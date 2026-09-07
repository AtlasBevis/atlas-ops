#!/usr/bin/env python3
"""Groups: list once → create missing → return full set."""

from __future__ import annotations

from dataclasses import dataclass

from common import (
    GROUPS_FILE, get_json, 
    load_yaml, post_json, require
)

@dataclass(frozen=True, slots=True)
class Group:
    group_id: str
    description: str | None = None

def list_groups(base: str) -> set[str]:
    data = get_json(f"{base}/groups")
    return {g["groupId"] for g in data.get("groups") or [] if g.get("groupId")}

def create_group(base: str, group_id: str, description: str | None = None) -> bool:
    body: dict = {"groupId": group_id}
    if description:
        body["description"] = description
    return post_json(f"{base}/groups", body) == 200

def load_groups() -> list[Group]:
    if not GROUPS_FILE.is_file():
        raise FileNotFoundError(f"Groups file not found: {GROUPS_FILE}")
    
    data = load_yaml(GROUPS_FILE)
    rows = require(data, "groups", GROUPS_FILE)
    groups: list[Group] = []
    for i, entry in enumerate(rows):
        if not isinstance(entry, dict) or not entry.get("groupId"):
            raise ValueError(f"Invalid group entry at index {i} in {GROUPS_FILE}")
        groups.append(Group(
            group_id=entry["groupId"], 
            description=entry.get("description"),
        ))
    return groups

def sync_groups(base: str) -> set[str]:
    desired = load_groups()
    existing = list_groups(base)
    created = 0
    for i, g in desired:
        if g.group_id in existing:
            continue
        if create_group(base, g.group_id, g.description):
            created += 1
        existing.add(g.group_id)

    print(f"[groups] listed={len(existing)} created={created}")
    return existing
