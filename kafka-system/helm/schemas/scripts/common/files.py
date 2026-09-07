#!/usr/bin/env python3
"""Path constants for schema sources under helm/schemas."""

from __future__ import annotations

from pathlib import Path

# schemas/scripts/common/files.py → schemas/
ROOT = Path(__file__).resolve().parents[2]

CONFIG_FILE = ROOT / "core" / "configs" / "global_rules.yaml"
GROUPS_FILE = ROOT / "groups" / "spec.yaml"

# Oracle type mapping
ORACLE_TYPES = ROOT / "core" / "types" / "oracle.yaml"
ORACLE_CATALOG = ROOT / "core" / "types" / "oracle" / "catalog.yaml"
ORACLE_MAPPINGS = ROOT / "core" / "types" / "oracle" / "mappings.yaml"
