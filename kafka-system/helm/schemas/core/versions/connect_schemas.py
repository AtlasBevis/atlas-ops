#!/usr/bin/env python3
"""Kafka Connect schema builders for Debezium ExtJsonConverter (JSON format)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from core.bootstrap.db import connector_source_artifact_id
from core.bootstrap.schemas import (
    db_source_schema,
    event_block_schema,
    heartbeat_key_schema,
    heartbeat_value_schema,
)
from core.common import SHARED_CATALOG, load_yaml

from .schemas import envelope_schema, key_schema, value_record_schema

_PRIMITIVES = {
    "null": "null",
    "boolean": "boolean",
    "int": "int32",
    "long": "int64",
    "float": "float32",
    "double": "float64",
    "bytes": "bytes",
    "string": "string",
}


def _record_fqn(schema: dict[str, Any]) -> str:
    connect_name = schema.get("connect.name")
    if connect_name:
        return str(connect_name)
    name = str(schema["name"])
    namespace = schema.get("namespace")
    return f"{namespace}.{name}" if namespace else name


@lru_cache(maxsize=1)
def _catalog_named_schemas() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for spec in load_yaml(SHARED_CATALOG).values():
        if not isinstance(spec, dict) or not spec.get("register"):
            continue
        schema = spec.get("schema")
        if not isinstance(schema, dict):
            continue
        names = {
            spec.get("connect.name"),
            spec.get("artifact"),
            _record_fqn(schema),
        }
        for name in names:
            if name:
                result[str(name)] = schema
    return result


def _named_schemas(extra: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {**_catalog_named_schemas(), **extra}


def _convert_type(
    avro_type: Any,
    named: dict[str, dict[str, Any]],
    *,
    optional: bool = False,
) -> dict[str, Any]:
    if isinstance(avro_type, list):
        non_null = [item for item in avro_type if item != "null"]
        if len(non_null) != 1 or len(non_null) == len(avro_type):
            raise ValueError(f"Unsupported Kafka Connect union: {avro_type!r}")
        return _convert_type(non_null[0], named, optional=True)

    if isinstance(avro_type, str):
        primitive = _PRIMITIVES.get(avro_type)
        if primitive is not None:
            return {"type": primitive, "optional": optional}
        schema = named.get(avro_type)
        if schema is None:
            raise ValueError(f"Unknown named Kafka Connect schema '{avro_type}'")
        return _convert_type(schema, named, optional=optional)

    if not isinstance(avro_type, dict):
        raise TypeError(f"Unsupported Kafka Connect schema node: {avro_type!r}")

    kind = avro_type.get("type")
    if kind == "record":
        result: dict[str, Any] = {
            "type": "struct",
            "fields": [
                _convert_field(field, named)
                for field in avro_type.get("fields", [])
            ],
            "optional": optional,
            "name": _record_fqn(avro_type),
        }
    elif kind == "array":
        result = {
            "type": "array",
            "items": _convert_type(avro_type["items"], named),
            "optional": optional,
        }
    elif kind == "map":
        result = {
            "type": "map",
            "keys": _convert_type(avro_type.get("keys", "string"), named),
            "values": _convert_type(avro_type["values"], named),
            "optional": optional,
        }
    else:
        result = _convert_type(kind, named, optional=optional)

    if avro_type.get("connect.name"):
        result["name"] = avro_type["connect.name"]
    if avro_type.get("connect.version") is not None:
        result["version"] = avro_type["connect.version"]
    if isinstance(avro_type.get("connect.parameters"), dict):
        result["parameters"] = avro_type["connect.parameters"]
    if avro_type.get("doc"):
        result["doc"] = avro_type["doc"]
    if "connect.default" in avro_type:
        result["default"] = avro_type["connect.default"]
    return result


def _convert_field(
    field: dict[str, Any],
    named: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    result = _convert_type(field["type"], named)
    result["field"] = field["name"]
    # Avro requires an explicit null default for nullable unions; Kafka
    # Connect represents that solely with optional=true.
    if field.get("default") is not None:
        result["default"] = field["default"]
    return result


def connect_key_schema(ns: str, fields: list[dict[str, Any]]) -> dict[str, Any]:
    schema = key_schema(ns, fields)
    return _convert_type(schema, _named_schemas({}))


def connect_envelope_schema(
    ns: str,
    fields: list[dict[str, Any]],
    connector: str,
) -> dict[str, Any]:
    value = value_record_schema(ns, fields)
    source = db_source_schema(connector)
    transaction = event_block_schema()
    named = _named_schemas(
        {
            _record_fqn(value): value,
            connector_source_artifact_id(connector): source,
            _record_fqn(transaction): transaction,
        }
    )
    schema = envelope_schema(
        ns,
        connector_source_artifact_id(connector),
        _record_fqn(value),
    )
    return _convert_type(schema, named)


def connect_heartbeat_key_schema() -> dict[str, Any]:
    return _convert_type(heartbeat_key_schema(), _named_schemas({}))


def connect_heartbeat_value_schema() -> dict[str, Any]:
    return _convert_type(heartbeat_value_schema(), _named_schemas({}))
