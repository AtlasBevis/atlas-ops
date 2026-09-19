#!/usr/bin/env python3
"""Path constants for schema sources under dp-schemas."""

from __future__ import annotations

from pathlib import Path

# core/files.py → dp-schemas/
ROOT = Path(__file__).resolve().parents[1]

CONFIG_FILE = ROOT / "configs" / "global_rules.yaml"

# Domain catalog
GROUPS_ROOT = ROOT / "domain"
GROUPS_FILE = GROUPS_ROOT / "index.yaml"

# Shared Avro/Connect catalog + per-connector type indexes
TYPES_ROOT = ROOT / "core" / "types"
SHARED_CATALOG = TYPES_ROOT / "shared" / "catalog.yaml"

ORACLE_TYPES = TYPES_ROOT / "oracle" / "index.yaml"
POSTGRES_TYPES = TYPES_ROOT / "postgres" / "index.yaml"
MYSQL_TYPES = TYPES_ROOT / "mysql" / "index.yaml"
SQLSERVER_TYPES = TYPES_ROOT / "sqlserver" / "index.yaml"
ORACLE_MAPPINGS = TYPES_ROOT / "oracle" / "mappings.yaml"
POSTGRES_MAPPINGS = TYPES_ROOT / "postgres" / "mappings.yaml"
MYSQL_MAPPINGS = TYPES_ROOT / "mysql" / "mappings.yaml"
SQLSERVER_MAPPINGS = TYPES_ROOT / "sqlserver" / "mappings.yaml"
