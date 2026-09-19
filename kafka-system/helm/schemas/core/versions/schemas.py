#!/usr/bin/env python3
"""Avro record builders for CDC Key / Value / Envelope."""

from __future__ import annotations

from typing import Any

from core.bootstrap.constants import BOOTSTRAP_VERSION, DEBEZIUM_GROUP
from core.bootstrap.db import connector_source_artifact_id


def key_schema(ns: str, fields: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "record",
        "name": "Key",
        "namespace": ns,
        "fields": fields,
        "connect.name": f"{ns}.Key",
    }


def value_record_schema(ns: str, fields: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "record",
        "name": "Value",
        "namespace": ns,
        "fields": fields,
        "connect.name": f"{ns}.Value",
    }


def envelope_schema(ns: str, source_type: str, value_fqn: str) -> dict[str, Any]:
    return {
        "type": "record",
        "name": "Envelope",
        "namespace": ns,
        "fields": [
            {"name": "before", "type": ["null", value_fqn], "default": None},
            {"name": "after", "type": ["null", value_fqn], "default": None},
            {"name": "source", "type": source_type},
            {"name": "transaction", "type": ["null", "event.block"], "default": None},
            {"name": "op", "type": "string"},
            {"name": "ts_ms", "type": ["null", "long"], "default": None},
            {"name": "ts_us", "type": ["null", "long"], "default": None},
            {"name": "ts_ns", "type": ["null", "long"], "default": None},
        ],
        "connect.version": 2,
        "connect.name": f"{ns}.Envelope",
    }


def bootstrap_reference(artifact_id: str) -> dict[str, str]:
    return {
        "name": artifact_id,
        "groupId": DEBEZIUM_GROUP,
        "artifactId": artifact_id,
        "version": BOOTSTRAP_VERSION,
    }


def debezium_shared_references(connector: str) -> list[dict[str, str]]:
    return [
        bootstrap_reference(connector_source_artifact_id(connector)),
        bootstrap_reference("event.block"),
    ]


def envelope_references(
    group_id: str,
    value_ns: str,
    value_version: str,
    connector: str,
    extra: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    value_id = f"{value_ns}.Value"
    return [
        {
            "name": value_id,
            "groupId": group_id,
            "artifactId": value_id,
            "version": value_version,
        },
        *debezium_shared_references(connector),
        *(extra or []),
    ]
