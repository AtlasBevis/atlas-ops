#!/usr/bin/env python3
"""Artifacts registered into group `debezium`."""

from __future__ import annotations

from typing import Any

from core.common import SHARED_CATALOG, load_yaml

from .constants import HEARTBEAT_KEY_ID, HEARTBEAT_VALUE_ID
from .db import Database, connector_namespace
from .schemas import (
    db_source_schema,
    event_block_schema,
    heartbeat_key_schema,
    heartbeat_value_schema,
    schema_change_key_schema,
    schema_change_value_schema,
    schema_history_change_schema,
    schema_history_column_schema,
    schema_history_table_schema,
    signal_key_schema,
    signal_value_schema,
)


def catalog_named_artifacts() -> list[tuple[str, str, dict[str, Any]]]:
    """Named Connect records from shared/catalog.yaml (VariableScaleDecimal, Geometry, …)."""
    data = load_yaml(SHARED_CATALOG)
    items: list[tuple[str, str, dict[str, Any]]] = []
    for key, spec in data.items():
        if not isinstance(spec, dict) or not spec.get("register"):
            continue
        schema = spec.get("schema")
        if not isinstance(schema, dict):
            raise ValueError(f"catalog '{key}' has register: true but no Avro schema")
        artifact = spec.get("artifact") or spec.get("connect.name")
        if not artifact:
            raise ValueError(f"catalog '{key}' is missing artifact / connect.name")
        items.append((str(artifact), f"Debezium {key}", schema))
    return items


def bootstrap_artifacts() -> list[tuple[str, str, dict[str, Any]]]:
    """(artifactId, description, avro schema) registered into group debezium."""
    items: list[tuple[str, str, dict[str, Any]]] = [
        *catalog_named_artifacts(),
        ("event.block", "Debezium transaction block", event_block_schema()),
        (HEARTBEAT_KEY_ID, "Heartbeat key", heartbeat_key_schema()),
        (HEARTBEAT_VALUE_ID, "Heartbeat value", heartbeat_value_schema()),
        ("io.debezium.signal.Key", "Signal key", signal_key_schema()),
        ("io.debezium.signal.Signal", "Signal value", signal_value_schema()),
        (
            "io.debezium.connector.schema.Column",
            "Schema history column",
            schema_history_column_schema(),
        ),
        (
            "io.debezium.connector.schema.Table",
            "Schema history table",
            schema_history_table_schema(),
        ),
        (
            "io.debezium.connector.schema.Change",
            "Schema history table change",
            schema_history_change_schema(),
        ),
    ]
    for db in Database:
        ns = connector_namespace(db.value)
        items.append((f"{ns}.Source", f"{db.value} source", db_source_schema(db.value)))
        items.append(
            (
                f"{ns}.SchemaChangeKey",
                f"{db.value} schema-change key",
                schema_change_key_schema(db.value),
            )
        )
        items.append(
            (
                f"{ns}.SchemaChangeValue",
                f"{db.value} schema-change value",
                schema_change_value_schema(db.value),
            )
        )
    return items
