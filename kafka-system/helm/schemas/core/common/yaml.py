#!/usr/bin/env python3
"""YAML load helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML object: {path}")
    return data


def require(data: dict, key: str, path: Path) -> Any:
    if key not in data or data[key] in (None, "", []):
        raise ValueError(f"Missing required key '{key}' in {path}")
    return data[key]
