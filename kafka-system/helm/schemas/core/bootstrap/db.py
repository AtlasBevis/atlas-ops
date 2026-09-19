#!/usr/bin/env python3
"""Canonical CDC databases (Debezium connectors)."""

from __future__ import annotations

from enum import Enum


class Database(str, Enum):
    """YAML `source.database`. Add a member when adding a connector."""

    ORACLE = "oracle"
    POSTGRES = "postgres"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"


# Extra YAML aliases → canonical Database
_DB_ALIASES: dict[str, Database] = {
    "oracle": Database.ORACLE,
    "postgres": Database.POSTGRES,
    "mysql": Database.MYSQL,
    "sqlserver": Database.SQLSERVER,
    "mssql": Database.SQLSERVER,
}

_CONNECTOR_NS: dict[Database, str] = {
    Database.ORACLE: "io.debezium.connector.oracle",
    Database.POSTGRES: "io.debezium.connector.postgresql",
    Database.MYSQL: "io.debezium.connector.mysql",
    Database.SQLSERVER: "io.debezium.connector.sqlserver",
}


def resolve_database(db: str) -> Database:
    if not isinstance(db, str) or not db.strip():
        raise ValueError("db must be a non-empty string")
    key = _DB_ALIASES.get(db.strip().lower())
    if key is None:
        allowed = ", ".join(sorted(_DB_ALIASES))
        raise ValueError(f"Unknown db '{db}'. Allowed: {allowed}")
    return key


def canonical_db(db: str) -> str:
    return resolve_database(db).value


def connector_namespace(connector: str) -> str:
    return _CONNECTOR_NS[resolve_database(connector)]


def connector_source_artifact_id(connector: str) -> str:
    return f"{connector_namespace(connector)}.Source"
