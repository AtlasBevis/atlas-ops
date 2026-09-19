#!/usr/bin/env python3
"""GET / PUT a version's lifecycle state (ENABLED, DEPRECATED, DISABLED, DRAFT).

Content is immutable once created (CI never rewrites a version's schema), but
*state* is not content — Apicurio treats ENABLED -> DEPRECATED -> DISABLED as a
separate, reversible transition. See "Managing schema lifecycle states":
https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-schema-lifecycle-best-practices.html
"""

from __future__ import annotations

from core.common import get_json, path_seg, put_json

from .models import VersionState


def _state_url(base: str, group_id: str, artifact_id: str, version: str) -> str:
    return (
        f"{base}/groups/{path_seg(group_id)}/artifacts/{path_seg(artifact_id)}"
        f"/versions/{path_seg(version)}/state"
    )


def get_version_state(base: str, group_id: str, artifact_id: str, version: str) -> str | None:
    """GET .../versions/{version}/state. None if the version doesn't exist yet."""
    data = get_json(_state_url(base, group_id, artifact_id, version), allow_404=True)
    state = data.get("state") if isinstance(data, dict) else None
    return str(state) if state else None


def update_version_state(
    base: str,
    group_id: str,
    artifact_id: str,
    version: str,
    state: str | VersionState,
) -> None:
    """PUT .../versions/{version}/state. Transitions are reversible."""
    value = state.value if isinstance(state, VersionState) else state
    put_json(_state_url(base, group_id, artifact_id, version), {"state": value})


def ensure_version_state(
    base: str,
    group_id: str,
    artifact_id: str,
    version: str,
    desired_state: str | VersionState,
) -> str:
    """Reconcile one version's state with the YAML `state:` field.

    Returns "updated" | "unchanged". No-op if the version isn't registered yet
    (a freshly created version already starts ENABLED, matching most YAML).
    """
    value = desired_state.value if isinstance(desired_state, VersionState) else desired_state
    current = get_version_state(base, group_id, artifact_id, version)
    if current is None or current == value:
        return "unchanged"
    update_version_state(base, group_id, artifact_id, version, value)
    return "updated"
