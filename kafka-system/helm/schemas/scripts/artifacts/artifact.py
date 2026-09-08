#!/usr/bin/env python3
"""Artifacts: validate domain specs against known groups + reference graph.

Hierarchy (Apicurio Registry v3):
  Group
    └── Artifact (artifactId, artifactType)
          └── Version (version, content, state)
                └── references[] → (name, groupId, artifactId, version)

Groups stay in groups/spec.yaml. Artifacts live as separate YAML files under
domain/ (and optionally schemas-gitops-style *.registry.yaml with
$type: artifact-v0). Do NOT nest artifacts inside the groups file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common import DOMAIN_ROOT, content_payload, get_json, load_yaml, path_seg, post_json, require
from artifacts.versions.version import Version, parse_version

ARTIFACT_TYPES = frozenset({
    "AVRO",
    "PROTOBUF",
    "JSON",
    "OPENAPI",
    "ASYNCAPI",
    "GRAPHQL",
    "KCONNECT",
    "WSDL",
    "XSD",
    "XML",
})

# Same length rule as Apicurio ArtifactId.
_ID_LEN = range(1, 513)


@dataclass(frozen=True, slots=True)
class Artifact:
    group_id: str
    artifact_id: str
    artifact_type: str
    versions: tuple[Version, ...]
    name: str | None = None
    description: str | None = None
    source: Path | None = None

    def __post_init__(self) -> None:
        for field_name, value in (
            ("groupId", self.group_id),
            ("artifactId", self.artifact_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
            if len(value) not in _ID_LEN:
                raise ValueError(f"{field_name} '{value}' must be 1–512 characters")

        if self.artifact_type not in ARTIFACT_TYPES:
            allowed = ", ".join(sorted(ARTIFACT_TYPES))
            raise ValueError(
                f"Invalid artifactType '{self.artifact_type}'. Allowed: {allowed}"
            )
        if not self.versions:
            raise ValueError(
                f"artifact '{self.group_id}/{self.artifact_id}' needs ≥1 version"
            )
        if self.name is not None and not isinstance(self.name, str):
            raise ValueError("name must be a string or omitted")
        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("description must be a string or omitted")

    @property
    def key(self) -> tuple[str, str]:
        return (self.group_id, self.artifact_id)

    def version_ids(self) -> set[str]:
        return {v.version for v in self.versions}


def _is_artifact_doc(data: dict) -> bool:
    type_ = data.get("$type")
    if type_ in ("artifact-v0", "artifact"):
        return True
    return (
        "artifactId" in data
        and "groupId" in data
        and "artifactType" in data
        and "versions" in data
    )


def discover_artifact_files() -> list[Path]:
    """Find artifact YAML under domain/."""
    if not DOMAIN_ROOT.is_dir():
        return []

    found: list[Path] = []
    for path in sorted(DOMAIN_ROOT.rglob("*.yaml")):
        if path.name in ("spec.yaml", "mappings.yaml", "catalog.yaml"):
            continue
        try:
            data = load_yaml(path)
        except ValueError:
            continue
        if _is_artifact_doc(data):
            found.append(path)
    return found


def load_artifact_file(path: Path) -> Artifact:
    data = load_yaml(path)
    if not _is_artifact_doc(data):
        raise ValueError(f"Not an artifact document: {path}")

    group_id = require(data, "groupId", path)
    artifact_id = require(data, "artifactId", path)
    artifact_type = require(data, "artifactType", path)
    raw_versions = require(data, "versions", path)
    if not isinstance(raw_versions, list):
        raise ValueError(f"'versions' must be a list in {path}")

    versions: list[Version] = []
    seen: set[str] = set()
    for i, entry in enumerate(raw_versions):
        if not isinstance(entry, dict):
            raise ValueError(f"versions[{i}] must be an object in {path}")
        ver = parse_version(entry, path=path, loc=f"versions[{i}]")
        if ver.version in seen:
            raise ValueError(
                f"Duplicate version '{ver.version}' for "
                f"{group_id}/{artifact_id} in {path}"
            )
        seen.add(ver.version)
        versions.append(ver)

    return Artifact(
        group_id=group_id,
        artifact_id=artifact_id,
        artifact_type=str(artifact_type).upper(),
        versions=tuple(versions),
        name=data.get("name"),
        description=data.get("description"),
        source=path,
    )


def validate_artifact_graph(
    artifacts: list[Artifact],
    known_groups: set[str],
) -> None:
    """Cross-check group membership + reference targets exist in the desired set."""
    by_key: dict[tuple[str, str], Artifact] = {}
    for art in artifacts:
        if art.group_id not in known_groups:
            raise ValueError(
                f"artifact '{art.group_id}/{art.artifact_id}' references unknown "
                f"groupId '{art.group_id}' (not in groups/spec.yaml)"
            )
        if art.key in by_key:
            other = by_key[art.key].source
            raise ValueError(
                f"Duplicate artifact {art.group_id}/{art.artifact_id}: "
                f"{art.source} and {other}"
            )
        by_key[art.key] = art

    # All version coordinates available in the desired graph.
    coords: set[tuple[str, str, str]] = set()
    for art in artifacts:
        for ver in art.versions:
            coords.add((art.group_id, art.artifact_id, ver.version))

    for art in artifacts:
        for ver in art.versions:
            for ref in ver.references:
                if ref.group_id not in known_groups:
                    raise ValueError(
                        f"reference '{ref.name}' in "
                        f"{art.group_id}/{art.artifact_id}@{ver.version} "
                        f"points to unknown groupId '{ref.group_id}'"
                    )
                if ref.coord not in coords:
                    raise ValueError(
                        f"reference '{ref.name}' in "
                        f"{art.group_id}/{art.artifact_id}@{ver.version} "
                        f"→ {ref.group_id}/{ref.artifact_id}@{ref.version} "
                        f"not found in desired artifacts"
                    )


def load_artifacts(known_groups: set[str]) -> list[Artifact]:
    """Load + validate all domain artifacts. Empty domain → empty list (OK)."""
    files = discover_artifact_files()
    artifacts = [load_artifact_file(p) for p in files]
    validate_artifact_graph(artifacts, known_groups)
    return artifacts


def topo_order(artifacts: list[Artifact]) -> list[Artifact]:
    """Order artifacts so referenced targets come before dependents.

    Used later by sync: create missing only, debezium/shared → record → key → envelope.
    """
    by_key = {a.key: a for a in artifacts}
    # Edge: artifact → depends on target artifact (ignore version for ordering)
    deps: dict[tuple[str, str], set[tuple[str, str]]] = {a.key: set() for a in artifacts}
    for art in artifacts:
        for ver in art.versions:
            for ref in ver.references:
                target = (ref.group_id, ref.artifact_id)
                if target == art.key:
                    raise ValueError(
                        f"Self-reference not allowed: "
                        f"{art.group_id}/{art.artifact_id} via '{ref.name}'"
                    )
                if target in by_key:
                    deps[art.key].add(target)

    ordered: list[Artifact] = []
    seen: set[tuple[str, str]] = set()
    stack: set[tuple[str, str]] = set()

    def visit(key: tuple[str, str]) -> None:
        if key in seen:
            return
        if key in stack:
            raise ValueError(f"Cyclic artifact references involving {key[0]}/{key[1]}")
        stack.add(key)
        for dep in sorted(deps[key]):
            visit(dep)
        stack.remove(key)
        seen.add(key)
        ordered.append(by_key[key])

    for key in sorted(by_key):
        visit(key)
    return ordered


def list_artifacts(base: str, group_id: str) -> set[str]:
    ids: set[str] = set()
    offset = 0
    limit = 100
    while True:
        url = (
            f"{base}/groups/{path_seg(group_id)}/artifacts"
            f"?limit={limit}&offset={offset}"
        )
        data = get_json(url, allow_404=True)
        rows = data.get("artifacts") if isinstance(data, dict) else data
        if not rows:
            break
        for row in rows:
            aid = row.get("artifactId") if isinstance(row, dict) else None
            if aid:
                ids.add(aid)
        if len(rows) < limit:
            break
        offset += limit
    return ids


def create_artifact(
    base: str,
    group_id: str,
    artifact_id: str,
    content: str | dict[str, Any],
    *,
    artifact_type: str = "AVRO",
    version: str = "1",
    name: str | None = None,
    description: str | None = None,
    references: list[dict[str, Any]] | None = None,
) -> bool:
    """POST /groups/{groupId}/artifacts (Apicurio Registry v3). 409 = already exists."""
    if isinstance(content, dict):
        content = json.dumps(content, ensure_ascii=False)
    payload = content_payload(content)
    if references:
        payload["references"] = references
    body: dict[str, Any] = {
        "artifactId": artifact_id,
        "artifactType": artifact_type,
        "name": name or artifact_id,
        "firstVersion": {
            "version": version,
            "content": payload,
        },
    }
    if description:
        body["description"] = description
    return post_json(f"{base}/groups/{path_seg(group_id)}/artifacts", body) in (200, 204)
