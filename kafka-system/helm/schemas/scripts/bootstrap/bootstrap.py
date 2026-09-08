from __future__ import annotations

from typing import Any

# Debezium 3.6.2 — SnapshotRecord + SchemaFactory.sourceInfoSchemaBuilder()
# https://debezium.io/documentation/reference/stable/connectors/oracle.html#oracle-schema-history-topic
_SNAPSHOT_ALLOWED = (
    "true,first,first_in_data_collection,last_in_data_collection,"
    "last,false,incremental"
)

_DB_ALIASES = {
    "oracle": "oracle",
    "postgres": "postgres",
    "mysql": "mysql",
    "mssql": "mssql",
}

_CONNECTOR_NS = {
    "oracle": "io.debezium.connector.oracle",
    "postgres": "io.debezium.connector.postgresql",
    "mysql": "io.debezium.connector.mysql",
    "mssql": "io.debezium.connector.sqlserver",
}


def _resolve_db(db: str) -> str:
    if not isinstance(db, str) or not db.strip():
        raise ValueError("db must be a non-empty string")
    key = _DB_ALIASES.get(db.strip().lower())
    if key is None:
        allowed = ", ".join(sorted(_DB_ALIASES))
        raise ValueError(f"Unknown db '{db}'. Allowed: {allowed}")
    return key


def _opt(avro_type: str) -> list[Any]:
    return ["null", avro_type]


def _opt_field(name: str, avro_type: str) -> dict[str, Any]:
    return {"name": name, "type": _opt(avro_type), "default": None}


def _opt_array_field(name: str, items: str | dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "type": ["null", {"type": "array", "items": items}],
        "default": None,
    }


def _snapshot_field() -> dict[str, Any]:
    return {
        "name": "snapshot",
        "type": [
            {
                "type": "string",
                "connect.version": 1,
                "connect.parameters": {"allowed": _SNAPSHOT_ALLOWED},
                "connect.default": "false",
                "connect.name": "io.debezium.data.Enum",
            },
            "null",
        ],
        "default": "false",
    }


def _common_source_fields() -> list[dict[str, Any]]:
    """Fields from AbstractSourceInfoStructMaker.commonSchemaBuilder()."""
    return [
        {"name": "version", "type": "string"},
        {"name": "connector", "type": "string"},
        {"name": "name", "type": "string"},
        {"name": "ts_ms", "type": "long"},
        _snapshot_field(),
        {"name": "db", "type": "string"},
        _opt_field("sequence", "string"),
        _opt_field("ts_us", "long"),
        _opt_field("ts_ns", "long"),
    ]


def _source_record(namespace: str, extra: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "record",
        "name": "Source",
        "namespace": namespace,
        "fields": _common_source_fields() + extra,
        "connect.version": 1,
        "connect.name": f"{namespace}.Source",
    }

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
        "doc": "Debezium signaling table",
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

def db_source_schema(db: str) -> dict[str, Any]:
    """Debezium envelope / schema-change `source` record (Avro + Connect metadata).

    Common fields: SchemaFactory.sourceInfoSchemaBuilder() (3.6.2).
    Extra fields: connector SourceInfoStructMaker (3.6.2).
    Canonical db keys: oracle, postgres, mysql, mssql.
    """
    key = _resolve_db(db)
    match key:
        case "oracle":
            return _source_record(
                _CONNECTOR_NS[key],
                [
                    {"name": "schema", "type": "string"},
                    {"name": "table", "type": "string"},
                    _opt_field("txId", "string"),
                    _opt_field("scn", "string"),
                    _opt_field("commit_scn", "string"),
                    _opt_field("lcr_position", "string"),
                    _opt_field("rs_id", "string"),
                    _opt_field("ssn", "long"),
                    _opt_field("redo_thread", "int"),
                    _opt_field("user_name", "string"),
                    _opt_field("redo_sql", "string"),
                    _opt_field("row_id", "string"),
                    _opt_field("commit_ts_ms", "long"),
                    _opt_field("start_scn", "string"),
                    _opt_field("start_ts_ms", "long"),
                    _opt_field("txSeq", "long"),
                ],
            )
        case "postgres":
            return _source_record(
                _CONNECTOR_NS[key],
                [
                    {"name": "schema", "type": "string"},
                    {"name": "table", "type": "string"},
                    _opt_field("txId", "long"),
                    _opt_field("lsn", "long"),
                    _opt_field("xmin", "long"),
                    _opt_field("origin", "string"),
                    _opt_field("origin_lsn", "long"),
                ],
            )
        case "mysql":
            return _source_record(
                _CONNECTOR_NS[key],
                [
                    _opt_field("table", "string"),
                    {"name": "server_id", "type": "long"},
                    _opt_field("gtid", "string"),
                    {"name": "file", "type": "string"},
                    {"name": "pos", "type": "long"},
                    {"name": "row", "type": "int"},
                    _opt_field("thread", "long"),
                    _opt_field("query", "string"),
                ],
            )
        case "mssql":
            return _source_record(
                _CONNECTOR_NS[key],
                [
                    {"name": "schema", "type": "string"},
                    {"name": "table", "type": "string"},
                    _opt_field("change_lsn", "string"),
                    _opt_field("commit_lsn", "string"),
                    _opt_field("event_serial_no", "long"),
                ],
            )
        case _:
            allowed = ", ".join(sorted(_DB_ALIASES))
            raise ValueError(f"Unknown db '{db}'. Allowed: {allowed}")


def schema_history_column_schema() -> dict[str, Any]:
    """io.debezium.connector.schema.Column — SchemaFactory.schemaHistoryColumnSchema()."""
    return {
        "type": "record",
        "name": "Column",
        "namespace": "io.debezium.connector.schema",
        "fields": [
            {"name": "name", "type": "string"},
            {"name": "jdbcType", "type": "int"},
            _opt_field("nativeType", "int"),
            {"name": "typeName", "type": "string"},
            _opt_field("typeExpression", "string"),
            _opt_field("charsetName", "string"),
            _opt_field("length", "int"),
            _opt_field("scale", "int"),
            {"name": "position", "type": "int"},
            _opt_field("optional", "boolean"),
            _opt_field("autoIncremented", "boolean"),
            _opt_field("generated", "boolean"),
            _opt_field("comment", "string"),
            _opt_field("defaultValueExpression", "string"),
            _opt_array_field("enumValues", "string"),
        ],
        "connect.version": 1,
        "connect.name": "io.debezium.connector.schema.Column",
    }


def schema_history_table_schema() -> dict[str, Any]:
    """io.debezium.connector.schema.Table — SchemaFactory.schemaHistoryTableSchema()."""
    return {
        "type": "record",
        "name": "Table",
        "namespace": "io.debezium.connector.schema",
        "fields": [
            _opt_field("defaultCharsetName", "string"),
            _opt_array_field("primaryKeyColumnNames", "string"),
            {
                "name": "columns",
                "type": {"type": "array", "items": schema_history_column_schema()},
            },
            _opt_field("comment", "string"),
        ],
        "connect.version": 1,
        "connect.name": "io.debezium.connector.schema.Table",
    }


def schema_history_change_schema() -> dict[str, Any]:
    """io.debezium.connector.schema.Change — one tableChanges[] entry."""
    return {
        "type": "record",
        "name": "Change",
        "namespace": "io.debezium.connector.schema",
        "fields": [
            {"name": "type", "type": "string"},
            {"name": "id", "type": "string"},
            {
                "name": "table",
                "type": ["null", schema_history_table_schema()],
                "default": None,
            },
        ],
        "connect.version": 1,
        "connect.name": "io.debezium.connector.schema.Change",
    }


def schema_change_key_schema(db: str) -> dict[str, Any]:
    """Schema change topic key: `{connector}.SchemaChangeKey` (databaseName)."""
    ns = _CONNECTOR_NS[_resolve_db(db)]
    return {
        "type": "record",
        "name": "SchemaChangeKey",
        "namespace": ns,
        "fields": [
            {"name": "databaseName", "type": "string"},
        ],
        "connect.version": 1,
        "connect.name": f"{ns}.SchemaChangeKey",
    }


def schema_change_value_schema(db: str) -> dict[str, Any]:
    """Schema change topic value: `{connector}.SchemaChangeValue`.

    Matches SchemaFactory.schemaHistoryConnectorValueSchema() in Debezium 3.6.2.
    `source` is the connector-specific Source record.
    """
    ns = _CONNECTOR_NS[_resolve_db(db)]
    return {
        "type": "record",
        "name": "SchemaChangeValue",
        "namespace": ns,
        "fields": [
            {"name": "source", "type": db_source_schema(db)},
            {"name": "ts_ms", "type": "long"},
            _opt_field("databaseName", "string"),
            _opt_field("schemaName", "string"),
            _opt_field("ddl", "string"),
            {
                "name": "tableChanges",
                "type": {"type": "array", "items": schema_history_change_schema()},
            },
        ],
        "connect.version": 1,
        "connect.name": f"{ns}.SchemaChangeValue",
    }