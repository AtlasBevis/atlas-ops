# Schema Registry CDC — agent handoff

Source of truth for **this pipeline**. Read this before changing anything under
`dp-schemas/`. Mapping details: [../core/types/README.md](../core/types/README.md).

Target stack:

- Debezium **3.6.1** (docs: `https://debezium.io/documentation/reference/3.6/connectors/…`)
- Apicurio Registry **v3** (`REGISTRY_URL` = `…/apis/registry/v3`)
- Connectors: `oracle` | `postgres` | `mysql` | `sqlserver`
- Schema lifecycle best practices (compat rules, refs, version states):
  `https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-schema-lifecycle-best-practices.html`

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

CI entry: `python main.py` (cwd = repo root). Package: `core/`.

```
sync_config → sync_bootstrap → groups = sync_groups → sync_artifacts(url, groups)
```

`REGISTRY_URL` is required. `SKIP_CONFIG_SYNC` skips global rules.

---

## Layout

```text
dp-schemas/
  main.py                     ← CI entry
  docs/CLAUDE.md              ← file này
  CLAUDE.md                   ← pointer
  .gitlab-ci.yml
  configs/
    global_rules.yaml         ← Registry global rules
  core/                       ← Python package + DB type mappings
    files.py                  ← path constants (GROUPS_ROOT = domain/)
    common/                   ← http.py, yaml.py
    config/                   ← rule_types.py, list.py, create.py, sync.py
    bootstrap/                ← db.py (Database enum), schemas.py, catalog.py, sync.py
    groups/                   ← models.py, list.py, create.py, load.py, sync.py
    artifacts/                ← artifact_types.py (format matrix), list/create/load/plan/sync
    versions/                 ← models.py, list.py, create.py, parse.py, plan.py, mapping.py, sync.py
    references/               ← models.py, list.py, payload.py
    types/
      shared/catalog.yaml     ← avro_ref → Avro / Connect
      {oracle,postgres,mysql,sqlserver}/
        index.yaml            ← connector metadata + Debezium modes
        mappings.yaml         ← DB type → Avro rules
  domain/                     ← source YAML (Apicurio groups)
    index.yaml                ← catalog groupId (bắt buộc)
    <folder>/<table>/
      index.yaml
      keys/vN.yaml
      values/vN.yaml
```

Folder names **do not** have to equal `groupId` or `table.name`.
Table indexes are discovered by glob: `domain/*/*/index.yaml` (exactly two levels).

---

## YAML contracts

### `domain/index.yaml`

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
  type: debezium          # debezium (CDC) | log (JSON Schema)
  format: avro            # avro | json; omitted defaults to json
  database: oracle        # CDC only: oracle | postgres | mysql | sqlserver
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

### Log event `index.yaml` (`source.type: log`)

JSON Schema (Apicurio `artifactType: JSON`). No DB types, no Envelope, no `.Value`.

```yaml
groupId: event
schema: app
topicPrefix: event.uat
source:
  type: log
  format: json              # optional; omitted format defaults to json
table:
  name: EventLogger
  description: EventLogger JSON payload
  key:                      # optional (value-only topic)
    description: JSON Key for EventLogger
    versions:
      - version: "1"
        state: ENABLED
  value:
    description: JSON Value for EventLogger
    versions:
      - version: "1"
        state: ENABLED
```

`source.database` and heartbeat are **not** allowed. Content files **are** JSON Schema
documents in YAML — not CDC `keys:` / `values:` column lists.

#### JSON Schema content file conventions (`keys/v1.yaml`, `values/v1.yaml` — log)

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: EventLogger
type: object
additionalProperties: false
required:
  - phone
  - log
properties:
  phone:
    type: string
    description: Customer phone number
  log:
    type: object
    additionalProperties: false
    properties: { ... }
```

| Key | Ý nghĩa |
| --- | --- |
| `$schema` | Khai báo dialect JSON Schema (`draft-07`) cho tooling/validator bên ngoài đọc đúng cú pháp. Apicurio không bắt buộc, nhưng nên giữ. |
| `title` | Tên tài liệu, thuần mô tả — không ảnh hưởng artifactId (`{topic}-key` / `{topic}-value`) hay validate. |
| `type` | Kiểu JSON Schema chuẩn: `object` \| `array` \| `string` \| `number` \| `integer` \| `boolean` \| `null` (hoặc mảng nhiều kiểu). Payload log luôn là `object`. **Nếu bỏ trống, generator tự set `type: object`** — xem `load_json_schema()` trong `core/versions/parse.py`. |
| `additionalProperties` | `false` = đóng (reject field lạ không khai trong `properties`); `true`/bỏ trống = mở, chấp nhận field lạ. Nên để `false` ở object root và các object lồng nhau để compatibility check ở Apicurio phát hiện thay đổi shape ngoài ý muốn. |
| `required` | Danh sách field bắt buộc — phải khớp tên trong `properties`. |
| `properties` | Field và kiểu tương ứng; object lồng nhau lặp lại cấu trúc này. |

Có thể bổ sung thêm (tuỳ nhu cầu, JSON Schema draft-07 hỗ trợ):

- `description` ở field hoặc root — tài liệu hoá thêm.
- `format` (`date-time`, `email`, …) cho field string có cấu trúc, ví dụ
  `time` / `created_at` / `updated_at` nên dùng `format: date-time` thay vì
  string tự do.
- `enum` cho field có tập giá trị cố định, ví dụ `level: [DEBUG, INFO, WARN, ERROR]`.
- `pattern` / `minLength` / `maxLength` cho string cần ràng buộc (ví dụ regex số điện thoại).
- `minimum` / `maximum` cho field số.
- `$id` nếu muốn định danh schema độc lập với artifactId.

**Validate ở đâu:**

1. Local/generator (`load_json_schema`): chỉ kiểm tra file không phải CDC
   `keys:`/`values:` list và default `type: object` khi thiếu — **không**
   validate đầy đủ cú pháp JSON Schema.
2. Server-side: Apicurio kiểm tra cú pháp JSON Schema thật khi `POST
   .../versions`, do global rule `VALIDITY: FULL` trong
   `configs/global_rules.yaml` (JSON artifact sai cú pháp → 400/409). Rule này
   chỉ có hiệu lực nếu CI **không** set `SKIP_CONFIG_SYNC=1` (xem phần
   Not implemented bên dưới).

### Column YAML (`keys/v1.yaml`, `values/v1.yaml`) — CDC

```yaml
keys:          # or values:
- name: ID
  type: NUMBER(10)      # DB type, not Avro — unless exact lowercase primitive
  nullable: false        # keys default NOT NULL; values default nullable
```

`type` is a **database** type (`NUMBER(10)`, `VARCHAR2(32)`, `DATETIME(6)`, …).
Mapping: `core/versions/mapping.py` + `core/types/<db>/mappings.yaml`.

For `format: avro`, these columns produce AVRO Key / `.Value` / Envelope
artifacts. For `format: json` (the default), they produce KCONNECT Key /
Envelope artifacts for Apicurio `ExtJsonConverter`; the row Value struct is
inlined into `before` and `after`.

Avro passthrough only if `type` is **exactly** one of:
`null` | `boolean` | `int` | `long` | `float` | `double` | `bytes` | `string`.
Uppercase `FLOAT` / `BOOLEAN` / `INT` are **DB** types, not Avro.

---

## Artifact naming

Topic: `{topicPrefix}.{schema}.{table.name}`  
Example: `cdc.prod.card-bo.MAIN.ACC_ACCOUNT`

Avro **namespace** (và artifact `.Value`) đổi `-` → `_` — xem
[avro-naming.md](avro-naming.md).

| ArtifactId | Avro record | Role |
| --- | --- | --- |
| `{topic}-key` | `Key` | PK |
| `{namespace}.Value` | `Value` | row payload (`before`/`after`) |
| `{topic}-value` | `Envelope` | Debezium envelope |

Example with `topicPrefix: cdc.prod.card-bo`:

```text
cdc.prod.card-bo.MAIN.ACC_ACCOUNT-key
cdc.prod.card_bo.MAIN.ACC_ACCOUNT.Value
cdc.prod.card-bo.MAIN.ACC_ACCOUNT-value
```

Log JSON (`source.type: log`, `artifactType: JSON`): topic formula is the same.
Artifacts are JSON Schema only — **no** `{namespace}.Value` and **no** Envelope:

```text
event.uat.app.EventLogger-key
event.uat.app.EventLogger-value
```

Heartbeat (only if `source.type=debezium` **and** `heartbeat: true` **and** non-empty `heartbeatPrefix`):

- Topic: `{heartbeatPrefix}.{topicPrefix}` e.g. `__heartbeat.prod.cdc.prod.card-bo`
- Artifacts: `{topic}-key` (`ServerNameKey`) + `{topic}-value` (`Heartbeat` / `ts_ms`)
- **No** `{topic}.Value` and no Envelope
- Deduped per group + heartbeat topic
- Uses the table format: `AVRO` for Avro CDC, `KCONNECT` for JSON CDC

Debezium JSON (`format: json`, Apicurio `artifactType: KCONNECT`) uses:

```text
{topic}-key                 # Kafka Connect Key struct
{topic}-value               # Kafka Connect Envelope; Value is inlined
```

There is no separate `.Value` artifact or Apicurio reference for KCONNECT.

Envelope fields: `before`, `after`, `source`, `transaction`, `op`, `ts_ms`, `ts_us`, `ts_ns`.  
`connect.version: 2`. Refs:

1. `{namespace}.Value` @ same version, same group
2. `debezium` / `io.debezium.connector.{oracle\|postgresql\|mysql\|sqlserver}.Source` @ `"1"`
3. `debezium` / `event.block` @ `"1"`

Named catalog types (`register: true`) add Apicurio refs on Key/Value fields
(e.g. `VariableScaleDecimal`, `Geometry`, `SparseVector`).

### Register order (must keep)

1. Global rules
2. Group `debezium` + bootstrap artifacts (including catalog named records)
3. Catalog groups from `domain/index.yaml`
4. Per table group: **empty** artifacts first, then versions
   (`AVRO`: **`.Value` → `-key` → `-value`**;
   `KCONNECT`/`JSON`: **`-value` → `-key`**)

CI never overwrites an existing version. To change a schema: bump version in
index + add `keys/vN.yaml` / `values/vN.yaml`.

---

## Version lifecycle: ENABLED / DEPRECATED / DISABLED

Reference: [Apicurio schema lifecycle best practices](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-schema-lifecycle-best-practices.html).

State is **not** content. Content is created once and never rewritten (see
above); state is reconciled on **every** run via `core/versions/state.py`
(`GET`/`PUT .../versions/{version}/state`), so it is safe and reversible.

| Phase | How this repo does it |
| --- | --- |
| Creation | `sync_config` (VALIDITY/COMPATIBILITY) → `sync_bootstrap` → empty artifact → first version, all `ENABLED` |
| Evolution | Bump `version:` + add `keys/vN.yaml` / `values/vN.yaml`; `BACKWARD_TRANSITIVE` rejects breaking changes |
| Deprecation | Edit the existing version's `state: DEPRECATED` in the table index YAML, commit — no content change |
| Retirement | Edit `state: DISABLED` after the deprecation window; artifact/version **deletion** is still out of scope (see below) |

Workflow to deprecate/disable an already-registered version:

1. Find the version entry under `table.key.versions[]` / `table.value.versions[]`
   in the table's `index.yaml` (do **not** touch its `content`/`vN.yaml`).
2. Change `state: ENABLED` → `state: DEPRECATED`. Give consumers a grace period
   (commonly 2–4 weeks).
3. After the grace period, change it to `state: DISABLED`.
4. Commit; CI's `sync_versions` PUTs the new state on the next run (`state_changed`
   counter in the `[artifacts]` log line).

Transitions are reversible (`DISABLED` → `ENABLED` is just editing YAML back).
Envelope versions mirror their paired `.Value` version's state (no separate
YAML field for Envelope). Bootstrap/heartbeat versions are always `ENABLED`.

---

## Core Python package — module rules

Convention the user enforced:

- Constants / dataclasses at the **top** of each file
- `sync_*` at the **end** of the module `main.py` calls
- No domain scanner, no `table.py` as the driver

| Module | Owns |
| --- | --- |
| `core/config/` | `RuleType` enum, list/create/update, `sync_config` |
| `core/bootstrap/` | `Database` enum (`sqlserver`; `mssql` alias), Source/heartbeat/signal/schema-history, catalog `register: true`, `sync_bootstrap` |
| `core/groups/` | Load `domain/index.yaml`; list/create; `sync_groups` last |
| `core/artifacts/` | `ArtifactType` / `SourceType`, TableIndex, list/create/plan, `sync_artifacts` last |
| `core/versions/` | Version model, Avro + JSON Schema planners, mapping, `sync_versions` last |
| `core/versions/mapping.py` | `parse_db_type` + first-matching mapping rule + catalog |
| `core/versions/state.py` | `ENABLED`/`DEPRECATED`/`DISABLED` GET/PUT + `ensure_version_state` (content-independent) |

Heartbeat supports Debezium `AVRO` and `KCONNECT`. `source.type: log` uses
`JSON` (`plan_log_versions`). `source.type: debezium` + `format: json` uses
`KCONNECT` (`plan_connect_versions`).

The `source.format` → `source.type` → `artifactType` matrix belongs to
`core/artifacts/artifact_types.py` (`_ARTIFACT_TYPE_BY_FORMAT`). When
`source.format` is omitted, Python always defaults it to `json`. To add a
format: update `ArtifactType` + that matrix, then the empty/version planners.

### `sync_groups` return set (known gap)

`filter_table_indexes` skips indexes whose `groupId` is not in the set passed
from `sync_groups`. **Intended:** that set is catalog IDs from `domain/index.yaml`
only (unknown `groupId` → skip + log, do not fail).

**Current code** returns the registry listing after creates (`existing`), so a
`groupId` that exists in the registry but is **not** in `domain/index.yaml`
would still sync. If you touch `groups/sync.py`, prefer:

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
| SQL Server | `DATETIME2` / `TIME` (no P, default 7) | nano types |
| SQL Server | `TIMESTAMP` / `ROWVERSION` | unsupported (not a datetime) |

Docs:

- Oracle: `#oracle-data-type-mappings`
- PostgreSQL: `#postgresql-data-types`
- MySQL: `#mysql-data-types`
- SQL Server: `#sqlserver-data-types`

Keep `documentation:` in `core/types/{connector}/index.yaml` on the **3.6** URLs, not `/stable/`.

---

## How to continue (playbooks)

### Add a CDC table

1. Ensure `groupId` exists in `domain/index.yaml`
2. Create `domain/<any-folder>/<table>/index.yaml`
3. Add `keys/v1.yaml` + `values/v1.yaml` with **DB** types
4. Do not hand-write Avro or Envelope YAML
5. Do not commit unless asked

### Add a JSON log event

1. Ensure `groupId` exists in `domain/index.yaml`
2. Create `domain/<folder>/<event>/index.yaml` with `source.type: log`
3. Add `values/v1.yaml` (and optional `keys/v1.yaml`) as **JSON Schema** YAML
4. Do not use DB types; do not expect Envelope / `.Value`
5. Do not commit unless asked

### Add / fix a DB type

1. Edit `core/types/<db>/mappings.yaml` (first match wins)
2. Add `avro_ref` to `shared/catalog.yaml` if missing
3. If `register: true`, bootstrap picks it up automatically (`catalog_named_artifacts`)
4. Do not change mapping “for the consumer” if it would diverge from Debezium 3.6.1

### Add a connector

1. `Database` member + alias in `core/bootstrap/db.py` (`_DB_ALIASES`, `_CONNECTOR_NS`)
2. Source extra fields in `core/bootstrap/schemas.py` (`db_source_schema`)
2. `core/types/<db>/index.yaml` + `mappings.yaml`
3. Paths in `core/files.py`
4. `_MAPPING_FILES` in `mapping.py`

### Change an existing schema

Bump `version` in the table index and add `vN.yaml`. Never mutate version `"1"`
in Git expecting CI to patch the registry.

### Deprecate / disable a schema version

1. In the table's `index.yaml`, find the version under `table.key.versions[]` /
   `table.value.versions[]` — do not touch its content file.
2. Set `state: DEPRECATED` (grace period), later `state: DISABLED`.
3. Commit. Do not bump `version:` — this is a state change, not a schema change.

---

## Not implemented / do not invent

- `source.signal` — unused (bootstrap already has Signal Key/Value artifacts)
- Updating a version's **content**, or deleting artifacts/versions (state
  transitions via `state:` in YAML ARE synced — see "Version lifecycle" above)
- INTEGRITY global rule (`ALL_REFS_MAPPED` would break heartbeat inlined fields)
- `new_table.py` — **removed**

---

## Leftovers (ignore or delete only if asked)

These are stale vs the current pipeline:

- `scripts/artifacts/versions/` (old nested copy)
- `scripts/artifacts/tables/`
- `scripts/common_pkg/`
- `scripts/validation/`
- `domain/group1/table1/table2/` stray file
- Root `README.md` historically pointed at `groups/`, `groups.registry.yaml`, `docs/schema-model.md`

Path constants: `core/files.py` (imported as `core.files`).
`core/common/__init__.py` re-exports them. Do not split a second source of paths.

---

## Invariants

1. Match Debezium 3.6.1, not a convenience Avro shape
2. Empty artifact before first version
3. `.Value` before Envelope that references it
4. Bootstrap group `debezium` before table groups that ref it
5. Consts/dataclasses at top; `sync_*` at end
6. Skip unknown catalog `groupId` (log, don’t fail) — restore if you fix `sync_groups`
7. No `references` in user YAML
8. Version `state:` is synced every run (PUT); version content is never rewritten
9. Do not commit unless the user asks
