#!/usr/bin/env python3
"""Create missing artifact versions, then reconcile version state."""

from __future__ import annotations

from typing import Any

from .create import ensure_version
from .models import VersionState
from .state import ensure_version_state


def sync_versions(
    base: str,
    group_id: str,
    jobs: list[dict[str, Any]],
) -> tuple[int, int, int]:
    """Create missing versions; reconcile ENABLED/DEPRECATED/DISABLED state.

    Content is created once and never rewritten. State is not content — it is
    checked (and PUT if different) on every run, so bumping `state:` in the
    table index YAML is enough to deprecate/disable an already-registered
    version. Returns (created, skipped, state_changed).
    """
    created = 0
    skipped = 0
    state_changed = 0
    for job in jobs:
        result = ensure_version(
            base,
            group_id,
            job["artifact_id"],
            job["content"],
            version=job["version"],
            description=job["description"],
            references=job["references"],
        )
        if result == "version":
            created += 1
        else:
            skipped += 1

        desired_state = job.get("state") or VersionState.ENABLED.value
        state_result = ensure_version_state(
            base, group_id, job["artifact_id"], job["version"], desired_state
        )
        if state_result == "updated":
            state_changed += 1

    return created, skipped, state_changed
