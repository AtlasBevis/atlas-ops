#!/usr/bin/env python3
"""Groups: list once → create missing → return full set."""

from __future__ import annotations

from common import ROOT, get_json, load_yaml, post_json, require

GROUPS_FILE = ROOT / "groups" / "groups.registry.yaml"


def list_groups(base: str) -> set[str]:
    data = get_json(f"{base}/groups")
    return {g["groupId"] for g in data.get("groups") or [] if g.get("groupId")}


def create_group(base: str, group_id: str, description: str | None = None) -> bool:
    body: dict = {"groupId": group_id}
    if description:
        body["description"] = description
    return post_json(f"{base}/groups", body) == 200

def validate_group_files() -> None: {
    
}

def sync_groups(base: str) -> set[str]:
    if not GROUPS_FILE.is_file():
        raise FileNotFoundError(f"Groups file not found: {GROUPS_FILE}")

    data = load_yaml(GROUPS_FILE)
    if data.get("$type") != "groups-v0":
        raise ValueError(f"Expected $type groups-v0 in {GROUPS_FILE}")
    desired = require(data, "groups", GROUPS_FILE)
    if not isinstance(desired, list):
        raise ValueError(f"'groups' must be a list in {GROUPS_FILE}")

    existing = list_groups(base)
    created = 0
    for i, entry in enumerate(desired):
        if not isinstance(entry, dict) or not entry.get("groupId"):
            raise ValueError(f"groups[{i}] missing groupId in {GROUPS_FILE}")
        gid = entry["groupId"]
        if gid in existing:
            continue
        if create_group(base, gid, entry.get("description")):
            created += 1
        existing.add(gid)

    print(f"[groups] listed={len(existing)} created={created} file={GROUPS_FILE.name}")
    return existing
