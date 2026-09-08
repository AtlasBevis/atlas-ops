#!/usr/bin/env python3
"""Map DB column types (Oracle/Postgres/MySQL/MSSQL) → Avro via core/types."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from bootstrap import BOOTSTRAP_VERSION, DEBEZIUM_GROUP, canonical_db
from common import (
    MSSQL_MAPPINGS,
    MYSQL_MAPPINGS,
    ORACLE_MAPPINGS,
    POSTGRES_MAPPINGS,
    SHARED_CATALOG,
    load_yaml,
    require,
)

AVRO_PRIMITIVES = frozenset(
    {"null", "boolean", "int", "long", "float", "double", "bytes", "string"}
)

_TYPE_RE = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z0-9]*(?: [A-Za-z0-9]+)*)\s*(?:\((?P<args>.*)\))?\s*$"
)

_MAPPING_FILES = {
    "oracle": ORACLE_MAPPINGS,
    "postgres": POSTGRES_MAPPINGS,
    "mysql": MYSQL_MAPPINGS,
    "mssql": MSSQL_MAPPINGS,
}

_NUMBER_TYPES = frozenset({"NUMBER", "DECIMAL", "NUMERIC", "DEC", "FIXED"})
_UNSIGNED_SUFFIX = " UNSIGNED"
_BIT_VARYING = frozenset({"BIT VARYING", "VARBIT"})
_BITS_UNBOUNDED = 2_147_483_647


def _is_temporal_type(name: str) -> bool:
    return (
        name.startswith("TIMESTAMP")
        or name.startswith("TIME")
        or name.startswith("DATETIME")
    )


@lru_cache(maxsize=1)
def _catalog() -> dict[str, Any]:
    data = load_yaml(SHARED_CATALOG)
    return {k: v for k, v in data.items() if isinstance(v, dict)}


@lru_cache(maxsize=8)
def _rules(connector: str) -> list[dict[str, Any]]:
    db = canonical_db(connector)
    path = _MAPPING_FILES[db]
    data = load_yaml(path)
    rules = require(data, "rules", path)
    if not isinstance(rules, list) or not rules:
        raise ValueError(f"'rules' must be a non-empty list in {path}")
    return rules


def parse_db_type(raw: str) -> dict[str, Any]:
    text = " ".join(str(raw).strip().split())
    unsigned = False
    if text.upper().endswith(_UNSIGNED_SUFFIX):
        unsigned = True
        text = text[: -len(_UNSIGNED_SUFFIX)].rstrip()
    match = _TYPE_RE.match(text)
    if not match:
        raise ValueError(f"Invalid DB type '{raw}'")
    name = " ".join(match.group("name").split()).upper()
    col: dict[str, Any] = {"type": name}
    if unsigned:
        col["unsigned"] = True
    args = match.group("args")
    if args is None:
        return col
    parts: list[int | None] = []
    for part in args.split(","):
        token = part.strip()
        if not token or token == "*":
            parts.append(None)
            continue
        try:
            parts.append(int(token))
        except ValueError as exc:
            raise ValueError(f"Invalid type parameter '{token}' in '{raw}'") from exc
    if name in _NUMBER_TYPES:
        if parts:
            col["precision"] = parts[0]
        if len(parts) > 1:
            col["scale"] = parts[1]
        elif parts and parts[0] is not None:
            col["scale"] = 0
    elif _is_temporal_type(name):
        if parts and parts[0] is not None:
            col["fractional_seconds"] = parts[0]
    elif name == "FLOAT" and parts:
        col["precision"] = parts[0]
    elif parts:
        col["length"] = parts[0]
    return col


def _cmp(value: int | None, cond: dict[str, Any]) -> bool:
    if "defined" in cond:
        if bool(cond["defined"]) != (value is not None):
            return False
    numeric = any(k in cond for k in ("gt", "gte", "lt", "lte"))
    if numeric and value is None:
        return False
    if value is None:
        return True
    if "gt" in cond and not value > cond["gt"]:
        return False
    if "gte" in cond and not value >= cond["gte"]:
        return False
    if "lt" in cond and not value < cond["lt"]:
        return False
    if "lte" in cond and not value <= cond["lte"]:
        return False
    return True


def _when_matches(when: object, col: dict[str, Any]) -> bool:
    if not when:
        return True
    if not isinstance(when, dict):
        return False
    for key, cond in when.items():
        if not isinstance(cond, dict):
            return False
        if key == "p_minus_s":
            precision = col.get("precision")
            scale = col.get("scale")
            width = None
            if isinstance(precision, int) and isinstance(scale, int):
                width = precision - scale
            if not _cmp(width, cond):
                return False
            continue
        if not _cmp(col.get(key), cond):
            return False
    return True


def _match_rule(col: dict[str, Any], rules: list[dict[str, Any]]) -> dict[str, Any]:
    source_type = col["type"]
    for rule in rules:
        types = rule.get("source_types") or []
        names = {str(t).upper() for t in types}
        if source_type not in names:
            continue
        if not _when_matches(rule.get("when"), col):
            continue
        return rule
    raise ValueError(f"No Avro mapping for {source_type} {col}")


def _catalog_type(
    avro_ref: str,
    col: dict[str, Any],
) -> tuple[Any, list[dict[str, str]]]:
    spec = _catalog().get(avro_ref)
    if not isinstance(spec, dict):
        raise ValueError(f"Unknown avro_ref '{avro_ref}' in catalog")
    if spec.get("register"):
        fqn = spec.get("connect.name") or spec.get("artifact")
        artifact = spec.get("artifact") or fqn
        group = spec.get("group") or DEBEZIUM_GROUP
        return str(fqn), [
            {
                "name": str(fqn),
                "groupId": str(group),
                "artifactId": str(artifact),
                "version": BOOTSTRAP_VERSION,
            }
        ]
    avro_type = spec.get("type")
    extra = {
        k: v
        for k, v in spec.items()
        if k not in {"type", "register", "group", "artifact", "schema", "doc"}
    }
    if avro_ref in AVRO_PRIMITIVES and not extra:
        return avro_type, []
    payload: dict[str, Any] = {"type": avro_type, **extra}
    if avro_ref == "decimal":
        precision = col.get("precision")
        scale = col.get("scale")
        payload["precision"] = precision if isinstance(precision, int) else 38
        payload["scale"] = scale if isinstance(scale, int) else 0
        payload.setdefault(
            "connect.parameters",
            {
                "scale": str(payload["scale"]),
                "connect.decimal.precision": str(payload["precision"]),
            },
        )
    elif avro_ref == "bits":
        length = col.get("length")
        if not isinstance(length, int):
            length = _BITS_UNBOUNDED if col.get("type") in _BIT_VARYING else 1
        payload["connect.parameters"] = {"length": str(length)}
    return payload, []


def map_column(
    entry: dict[str, Any],
    *,
    path: Path,
    connector: str,
    default_nullable: bool,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    name = require(entry, "name", path)
    raw_type = require(entry, "type", path)
    if not isinstance(raw_type, str) or not raw_type.strip():
        raise ValueError(f"Column '{name}' type must be a string in {path}")

    if raw_type.strip() in AVRO_PRIMITIVES:
        avro_type: Any = raw_type.strip()
        refs: list[dict[str, str]] = []
    else:
        col = parse_db_type(raw_type)
        for key in ("precision", "scale", "length", "fractional_seconds", "unsigned"):
            if key in entry:
                col[key] = entry[key]
        rule = _match_rule(col, _rules(connector))
        if rule.get("supported") is False:
            notes = rule.get("notes") or "not supported"
            raise ValueError(
                f"Column '{name}' type '{raw_type}' is not mapped ({notes}) in {path}"
            )
        avro_ref = require(rule, "avro_ref", path)
        avro_type, refs = _catalog_type(str(avro_ref), col)
        extra = rule.get("extra")
        if isinstance(extra, dict) and isinstance(avro_type, dict):
            avro_type = {**avro_type, **extra}

    nullable = entry.get("nullable", default_nullable)
    field: dict[str, Any] = {"name": name}
    if nullable:
        field["type"] = ["null", avro_type]
        field["default"] = None if "default" not in entry else entry.get("default")
    else:
        field["type"] = avro_type
        if "default" in entry:
            field["default"] = entry["default"]
    return field, refs
