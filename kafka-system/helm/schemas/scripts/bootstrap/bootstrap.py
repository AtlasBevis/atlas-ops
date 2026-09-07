from __future__ import annotations

import json
from typing import Any


# SOURCE_SCHEMAS = {
#     "oracle": (oracle_source_schema, "io.debezium.connector.oracle.Source"),
#     "sqlserver": (sqlserver_source_schema, "io.debezium.connector.sqlserver.Source"),
# }

def event_block_schema() -> dict[str, Any]:
    return {
        "type": "record",
        "name": "block",
        "namespace": "event",
        "doc": "Debezium transaction block metadata",
        "fields": [
            {"name": "id", "type": "string"},
            {"name": "total_order", "type": "long"},
            {"name": "data_collection_order", "type": "long"},
        ],
        "connect.version": 1,
        "connect.name": "event.block",
    }

def heartbeat_key_schema() -> dict[str, Any]:
    return {
        "type": "record",
        "name": "ServerNameKey",
        "namespace": "io.debezium.connector.common",
        "fields": [
            {"name": "serverName", "type": "string"},
        ],
        "connect.version": 1,
        "connect.name": "io.debezium.connector.common.ServerNameKey",
    }

def heartbeat_value_schema() -> dict[str, Any]:
    return {
        "type": "record",
        "name": "Heartbeat",
        "namespace": "io.debezium.connector.common",
        "fields": [
            {"name": "ts_ms", "type": "long"},
        ],
        "connect.version": 1,
        "connect.name": "io.debezium.connector.common.Heartbeat",
    }

def signal_value_schema() -> dict[str, Any]:
    return {
        "type": "record",
        "name": "Signal",
        "namespace": "io.debezium.signal",
        "doc": "Debezium signaling table row (id, type, data)",
        "fields": [
            {"name": "id", "type": "string"},
            {"name": "type", "type": "string"},
            {"name": "data", "type": ["null", "string"], "default": None},
        ],
        "connect.version": 1,
        "connect.name": "io.debezium.signal.Signal",
    }

def signal_key_schema() -> dict[str, Any]:
    return {
        "type": "record",
        "name": "Key",
        "namespace": "io.debezium.signal",
        "fields": [
            {"name": "id", "type": "string"},
        ],
        "connect.version": 1,
        "connect.name": "io.debezium.signal.Key",
    }