---
name: schema-registry-cdc
description: >-
  Maintains the Atlas Ops Schema Registry CDC pipeline under kafka-system/helm/schemas
  (Debezium 3.6.1, Apicurio v3, Oracle/Postgres/MySQL/MSSQL Avro). Use when adding CDC
  tables, groups, key/value YAML, type mappings, bootstrap artifacts, envelope/heartbeat
  schemas, or changing scripts/main.py, mapping.py, artifact.py, version.py, or
  core/types.
---

# Schema Registry CDC

Before any edit under `kafka-system/helm/schemas/`, read:

- [docs/CLAUDE.md](../../../kafka-system/helm/schemas/docs/CLAUDE.md) — contracts, CI order, gaps, playbooks
- [core/types/README.md](../../../kafka-system/helm/schemas/core/types/README.md) — DB → Avro rules

## Hard rules

1. Match **Debezium 3.6.1** (`documentation/reference/3.6/…`), not `/stable/` and not consumer-convenience types.
2. Column YAML uses **DB types** (`NUMBER(10)`, `VARCHAR2`, `DATETIME(6)`). Avro passthrough only for exact lowercase primitives.
3. Do not put `references` in table YAML. Envelope refs are derived.
4. CI creates **missing** groups/artifacts/versions only. Schema change = **new version file**, not mutate v1 in registry.
5. Register order: config → bootstrap (`debezium`) → groups → empty artifacts → versions `.Value` → `-key` → `-value`.
6. Consts/dataclasses at top of each script; `sync_*` at the end of the module `main.py` calls.
7. `source.signal` is unused. Do not implement it unless asked.
8. Do not commit unless the user asks.

## Touch map

| Change | Files |
| --- | --- |
| New table | `groups/index.yaml` + `groups/<folder>/<table>/index.yaml` + `keys/vN.yaml` + `values/vN.yaml` |
| New/fix DB type | `core/types/<db>/mappings.yaml`, maybe `shared/catalog.yaml` |
| Shared Debezium records | `scripts/bootstrap/bootstrap.py` (catalog `register: true` is auto-loaded) |
| Artifact naming / heartbeat | `scripts/artifacts/artifact.py` + `scripts/versions/version.py` |
| CI flow | `scripts/main.py` |

## Defaults assumed in mappings

`decimal.handling.mode=precise`, `binary.handling.mode=bytes`, `time.precision.mode=adaptive` (MySQL: `adaptive_time_microseconds`).
