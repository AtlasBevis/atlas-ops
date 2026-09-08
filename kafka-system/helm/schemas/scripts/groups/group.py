#!/usr/bin/env python3
"""
Manifest group definitions

reference: https://www.apicur.io/registry/docs/apicurio-registry/3.0.x/assets-attachments/registry-rest-api.htm#tag/Groups
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from common import (
    GROUPS_FILE,
    get_json,
    load_yaml,
    post_json,
    require,
)

# GroupId pattern ^.{1,512}$;
GROUP_ID_RE = re.compile(r"^.{1,512}$")
RESERVED_GROUP_IDS = frozenset({"default"})


@dataclass(frozen=True, slots=True)
class Group:
    group_id: str
    description: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.group_id, str):
            raise ValueError(f"groupId must be a string, got {type(self.group_id).__name__}")
        
        if not GROUP_ID_RE.fullmatch(self.group_id):
            raise ValueError(
                f"Invalid groupId '{self.group_id}': must be 1-512 characters"
            )
        
        if self.group_id in RESERVED_GROUP_IDS:
            raise ValueError(f"groupId '{self.group_id}' is reserved")
        
        if self.description is not None and not isinstance(self.description, str):
            raise ValueError(
                f"description for groupId '{self.group_id}' must be a string or omitted"
            )


def list_groups(base: str) -> set[str]:
    """ 
    Returns a list of all groups. This list is paged.
    
    GET /groups
    """
    data = get_json(f"{base}/groups")
    return {g["groupId"] for g in data.get("groups") or [] if g.get("groupId")}


def create_group(base: str, group_id: str, description: str | None = None) -> bool:
    """
    Creates a new group.

    POST /groups
    """
    body: dict = {"groupId": group_id}
    if description:
        body["description"] = description
    return post_json(f"{base}/groups", body) == 200

def load_groups() -> list[Group]:
    """Load groups from groups/index.yaml."""
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
