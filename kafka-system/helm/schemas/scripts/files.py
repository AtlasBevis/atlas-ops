#!/usr/bin/env python3
"""Path constants for schema sources under helm/schemas."""

from __future__ import annotations

from pathlib import Path

# schemas/scripts/files.py → schemas/
ROOT = Path(__file__).resolve().parents[1]

CONFIG_FILE = ROOT / "core" / "configs" / "global_rules.yaml"

# Groups
GROUPS_ROOT = ROOT / "groups"
GROUPS_FILE = GROUPS_ROOT / "index.yaml"

# Shared Avro/Connect catalog + per-connector type indexes
TYPES_ROOT = ROOT / "core" / "types"
SHARED_CATALOG = TYPES_ROOT / "shared" / "catalog.yaml"
ORACLE_TYPES = TYPES_ROOT / "oracle.yaml"
POSTGRES_TYPES = TYPES_ROOT / "postgres.yaml"
MYSQL_TYPES = TYPES_ROOT / "mysql.yaml"
MSSQL_TYPES = TYPES_ROOT / "mssql.yaml"
ORACLE_MAPPINGS = TYPES_ROOT / "oracle" / "mappings.yaml"
POSTGRES_MAPPINGS = TYPES_ROOT / "postgres" / "mappings.yaml"
MYSQL_MAPPINGS = TYPES_ROOT / "mysql" / "mappings.yaml"
MSSQL_MAPPINGS = TYPES_ROOT / "mssql" / "mappings.yaml"
