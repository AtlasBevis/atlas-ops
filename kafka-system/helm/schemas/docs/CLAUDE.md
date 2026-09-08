# Schema Registry CDC — agent handoff

Source of truth for **this pipeline**. Read this before changing anything under
`kafka-system/helm/schemas/`. Mapping details: [../core/types/README.md](../core/types/README.md).

Target stack:

- Debezium **3.6.1** (docs: `https://debezium.io/documentation/reference/3.6/connectors/…`)
- Apicurio Registry **v3** (`REGISTRY_URL` = `…/apis/registry/v3`)
- Connectors: `oracle` | `postgres` | `mysql` | `mssql`

Connector config assumed when generating Avro (must match production):

| Connector | `decimal.handling.mode` | `time.precision.mode` | Other |
| --- | --- | --- | --- |
| Oracle | `precise` | `adaptive` | `interval.handling.mode=numeric`, `binary.handling.mode=bytes` |
| PostgreSQL | `precise` | `adaptive` | same + `hstore.handling.mode=json` |
| MySQL | `precise` | `adaptive_time_microseconds` | `binary.handling.mode=bytes` |
| SQL Server | `precise` | `adaptive` | `binary.handling.mode=bytes` |

If production uses another mode (`connect`, `string`, `isostring`, …), mappings
**must** change or generated Avro will not match runtime.

---

## What this system does

Git is the source of truth. CI **creates missing** groups / empty artifacts /
versions. It does **not** update or delete existing versions (409 / already-exists = skip).

Connector should run with `auto-register=false` + `find-latest=true`.

CI entry: `scripts/main.py` (cwd = `scripts/`, `PYTHONPATH` = that dir).

```
sync_config → sync_bootstrap → groups = sync_groups → sync_artifacts(url, groups)
```

`REGISTRY_URL` is required. `SKIP_CONFIG_SYNC` skips global rules.

---

## Layout

```text
kafka-system/helm/schemas/
  docs/CLAUDE.md              ← file này
  CLAUDE.md                   ← pointer
  .gitlab-ci.yaml
  core/
    configs/global_rules.yaml
    types/
      shared/catalog.yaml     ← avro_ref → Avro / Connect
      {oracle,postgres,mysql,mssql}.yaml
      {oracle,postgres,mysql,mssql}/mappings.yaml
  groups/
    index.yaml                ← catalog groupId (bắt buộc)
    <folder>/<table>/
      index.yaml
      keys/vN.yaml
      values/vN.yaml
  scripts/
    main.py
    files.py                  ← path constants
    common/                   ← HTTP + YAML helpers
    config/rules.py           ← sync_config (cuối file)
    bootstrap/bootstrap.py
    groups/group.py
    artifacts/artifact.py
    versions/version.py
    versions/mapping.py       ← DB type → Avro
    references/reference.py
```

Folder names **do not** have to equal `groupId` or `table.name`.
Table indexes are discovered by glob: `groups/*/*/index.yaml` (exactly two levels).

---

## YAML contracts

### `groups/index.yaml`

```yaml
groups:
  - groupId: group1
    description: group for group1 (Oracle)
```

`sync_groups` creates missing groups. `groupId` `default` is reserved.

### Table `index.yaml`

```yaml
groupId: group1
schema: MAIN
topicPrefix: cdc.group1
source:
  type: debezium          # debezium | log
  database: oracle        # oracle | postgres | mysql | mssql
  signal: true           # parsed but NOT implemented
  heartbeat: true        # default false
  heartbeatPrefix: __heartbeat.uat   # required for heartbeat artifacts
table:
  name: TABLE1
  description: ...
  key:
    description: ...
    versions:
      - version: "1"
        state: ENABLED     # ENABLED | DISABLED | DEPRECATED | DRAFT
  value:
    description: ...
    versions:
      - version: "1"
        state: ENABLED
```

Do **not** put `references` in YAML. Envelope / Source / `event.block` refs are
derived from `source.type` + `source.database`.

Key/value content files are **not** listed in the index. They are resolved as:

- `keys/v{version}.yaml`  (or `v1.yaml` if version is `"1"`; `version_filename()`)
- `values/v{version}.yaml`

### Column YAML (`keys/v1.yaml`, `values/v1.yaml`)

```yaml
keys:          # or values:
- name: ID
  type: NUMBER(10)      # DB type, not Avro — unless exact lowercase primitive
  nullable: false        # keys default NOT NULL; values default nullable
```

`type` is a **database** type (`NUMBER(10)`, `VARCHAR2(32)`, `DATETIME(6)`, …).
Mapping: `scripts/versions/mapping.py` + `core/types/<db>/mappings.yaml`.

Avro passthrough only if `type` is **exactly** one of:
`null` | `boolean` | `int` | `long` | `float` | `double` | `bytes` | `string`.
Uppercase `FLOAT` / `BOOLEAN` / `INT` are **DB** types, not Avro.

---

## Artifact naming

Topic: `{topicPrefix}.{schema}.{table.name}`  
Example: `cdc.group1.MAIN.TABLE1`

Per table (same group as `groupId`):

| ArtifactId | Avro record | Role |
| --- | --- | --- |
| `{topic}-key` | `Key` | PK |
| `{topic}.Value` | `Value` | row payload (`before`/`after`) |
| `{topic}-value` | `Envelope` | Debezium envelope |

Heartbeat (only if `source.type=debezium` **and** `heartbeat: true` **and** non-empty `heartbeatPrefix`):

- Topic: `{heartbeatPrefix}.{topicPrefix}` e.g. `__heartbeat.uat.cdc.group1`
- Same three artifact suffixes; Key field `serverName`; Value field `ts_ms`
- Deduped per group + heartbeat topic

Envelope fields: `before`, `after`, `source`, `transaction`, `op`, `ts_ms`, `ts_us`, `ts_ns`.  
`connect.version: 2`. Refs:

1. `{topic}.Value` @ same version, same group
2. `debezium` / `io.debezium.connector.{oracle\|postgresql\|mysql\|sqlserver}.Source` @ `"1"`
3. `debezium` / `event.block` @ `"1"`

Heartbeat envelope also refs `io.debezium.connector.common.Heartbeat`.

Named catalog types (`register: true`) add Apicurio refs on Key/Value fields
(e.g. `VariableScaleDecimal`, `Geometry`, `SparseVector`).

### Register order (must keep)

1. Global rules
2. Group `debezium` + bootstrap artifacts (including catalog named records)
3. Catalog groups from `groups/index.yaml`
4. Per table group: **empty** artifacts first, then versions **`.Value` → `-key` → `-value`**

CI never overwrites an existing version. To change a schema: bump version in
index + add `keys/vN.yaml` / `values/vN.yaml`.

---

## Scripts — module rules

Convention the user enforced:

- Constants / dataclasses at the **top** of each file
- `sync_*` at the **end** of the module `main.py` calls
- No domain scanner, no `table.py` as the driver

| Module | Owns |
| --- | --- |
| `config/rules.py` | Global VALIDITY/COMPATIBILITY (INTEGRITY not in YAML) |
| `bootstrap/bootstrap.py` | Group `debezium`, Source/Envelope shared types, heartbeat/signal/schema-history, **catalog `register: true` records** |
| `groups/group.py` | Load `groups/index.yaml` only; create missing; return group id set (see gap below) |
| `artifacts/artifact.py` | TableIndex, glob, empty `-key`/`.Value`/`-value`, heartbeat empties, `sync_artifacts` last |
| `versions/version.py` | Version model, Avro Key/Value/Envelope, `plan_versions`, `plan_heartbeat_versions`, `sync_versions` last |
| `versions/mapping.py` | `parse_db_type` + first-matching mapping rule + catalog |

`source.type: log` is allowed in YAML but still follows the Debezium artifact/version path (needs `database`). Heartbeat only for `debezium`.

### `sync_groups` return set (known gap)

`filter_table_indexes` skips indexes whose `groupId` is not in the set passed
from `sync_groups`. **Intended:** that set is catalog IDs from `groups/index.yaml`
only (unknown `groupId` → skip + log, do not fail).

**Current code** returns the registry listing after creates (`existing`), so a
`groupId` that exists in the registry but is **not** in `groups/index.yaml`
would still sync. If you touch `group.py`, prefer:

```python
return {g.group_id for g in desired}
```

and keep the skip log:

```text
[artifacts] skip <path>: unknown groupId '...'
```

---

## Type mapping (Debezium 3.6.1)

Do **not** invent consumer-friendly types. Match Debezium emit types.

- Rules: first match in `core/types/<db>/mappings.yaml` wins
- `supported: false` → generator **fails** (do not silently drop the column)
- Avro has no INT8/INT16 → use `int`
- `register: true` catalog types **must** also be in `bootstrap_artifacts()` via `catalog_named_artifacts()`

High-signal mappings:

| DB | Input | Avro / Connect |
| --- | --- | --- |
| Oracle | `NUMBER(10)` (scale 0, P−S=10) | `long` |
| Oracle | `NUMBER` / `NUMBER(P,*)` | `VariableScaleDecimal` |
| Oracle | `TIMESTAMP` (no precision, default 6) | `MicroTimestamp` |
| Oracle | `DATE` | `Timestamp` (ms) |
| Oracle | `RAW` | bytes |
| Oracle | `XMLTYPE` | `io.debezium.data.Xml` |
| Oracle | `INTERVAL …` | `MicroDuration` **double** |
| Oracle | `BOOLEAN` / `VECTOR` / `LONG` / `BFILE` | unsupported |
| Postgres | `INTERVAL` | `MicroDuration` **long** |
| Postgres | `NUMERIC` (no scale) | `VariableScaleDecimal` |
| Postgres | `VECTOR` / `HALFVEC` / `SPARSEVEC` | DoubleVector / FloatVector / SparseVector |
| MySQL | `DATETIME` (no fsp, default 0) | `Timestamp` (ms) |
| MySQL | `DATETIME(4–6)` | `MicroTimestamp` |
| MySQL | `FLOAT` (no P) | float; `FLOAT(P≥24)` double |
| MySQL | `TIMESTAMP` | `ZonedTimestamp` |
| MSSQL | `DATETIME2` / `TIME` (no P, default 7) | nano types |
| MSSQL | `TIMESTAMP` / `ROWVERSION` | unsupported (not a datetime) |

Docs:

- Oracle: `#oracle-data-type-mappings`
- PostgreSQL: `#postgresql-data-types`
- MySQL: `#mysql-data-types`
- SQL Server: `#sqlserver-data-types`

Keep `documentation:` in `core/types/{connector}.yaml` on the **3.6** URLs, not `/stable/`.

---

## How to continue (playbooks)

### Add a CDC table

1. Ensure `groupId` exists in `groups/index.yaml`
2. Create `groups/<any-folder>/<table>/index.yaml`
3. Add `keys/v1.yaml` + `values/v1.yaml` with **DB** types
4. Do not hand-write Avro or Envelope YAML
5. Do not commit unless asked

### Add / fix a DB type

1. Edit `core/types/<db>/mappings.yaml` (first match wins)
2. Add `avro_ref` to `shared/catalog.yaml` if missing
3. If `register: true`, bootstrap picks it up automatically (`catalog_named_artifacts`)
4. Do not change mapping “for the consumer” if it would diverge from Debezium 3.6.1

### Add a connector

1. Alias in `bootstrap._DB_ALIASES` + `_CONNECTOR_NS` + `_DBS`
2. `core/types/<db>.yaml` + `mappings.yaml`
3. Paths in `scripts/files.py`
4. `_MAPPING_FILES` in `mapping.py`

### Change an existing schema

Bump `version` in the table index and add `vN.yaml`. Never mutate version `"1"`
in Git expecting CI to patch the registry.

---

## Not implemented / do not invent

- `source.signal` — unused (bootstrap already has Signal Key/Value artifacts)
- Separate `source.type: log` code path (YAML allows it; still Debezium-shaped)
- Updating or deleting registry versions
- INTEGRITY global rule (`ALL_REFS_MAPPED` would break heartbeat inlined fields)
- `new_table.py` / `domain/` tree — **removed**; README used to mention them

---

## Leftovers (ignore or delete only if asked)

These are stale vs the current pipeline:

- `scripts/artifacts/versions/` (old nested copy)
- `scripts/artifacts/tables/`
- `scripts/common_pkg/`
- `scripts/validation/`
- `groups/group1/table1/table2/` stray file
- Root `README.md` historically pointed at `domain/`, `groups.registry.yaml`, `docs/schema-model.md`

Path constants: `scripts/files.py` (imported as `files` when cwd is `scripts/`).
`scripts/common/__init__.py` re-exports them. Do not split a second source of paths.

---

## Invariants

1. Match Debezium 3.6.1, not a convenience Avro shape
2. Empty artifact before first version
3. `.Value` before Envelope that references it
4. Bootstrap group `debezium` before table groups that ref it
5. Consts/dataclasses at top; `sync_*` at end
6. Skip unknown catalog `groupId` (log, don’t fail) — restore if you fix `sync_groups`
7. No `references` in user YAML
8. Do not commit unless the user asks
