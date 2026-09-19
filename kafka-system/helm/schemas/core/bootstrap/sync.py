#!/usr/bin/env python3
"""Create group `debezium` and shared artifacts."""

from __future__ import annotations

from core.groups.create import create_group
from core.groups.list import list_groups

from .catalog import bootstrap_artifacts
from .constants import BOOTSTRAP_VERSION, DEBEZIUM_GROUP, DEBEZIUM_GROUP_DESCRIPTION


def sync_bootstrap(base: str) -> None:
    """Create group `debezium` if missing, then create missing shared artifacts."""
    # Lazy import: core.artifacts -> core.versions.plan -> core.versions.mapping
    # -> core.bootstrap.constants, so a module-level import here would be
    # circular whenever core.bootstrap is imported before core.artifacts
    # finishes initializing (e.g. `import core.versions` directly).
    from core.artifacts.create import create_artifact
    from core.artifacts.list import list_artifacts

    existing_groups = list_groups(base)
    created_group = 0
    if DEBEZIUM_GROUP not in existing_groups:
        if create_group(base, DEBEZIUM_GROUP, DEBEZIUM_GROUP_DESCRIPTION):
            created_group = 1

    desired = bootstrap_artifacts()
    existing = list_artifacts(base, DEBEZIUM_GROUP)
    created = 0
    for artifact_id, description, schema in desired:
        if artifact_id in existing:
            continue
        if create_artifact(
            base,
            DEBEZIUM_GROUP,
            artifact_id,
            schema,
            version=BOOTSTRAP_VERSION,
            description=description,
        ):
            created += 1
        existing.add(artifact_id)

    print(
        f"[bootstrap] created_group={created_group} "
        f"created_artifacts={created}"
    )
