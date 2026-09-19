# Schema lifecycle — compliance with Apicurio best practices

Source: [Apicurio Registry — Schema lifecycle best practices (3.3.x)](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-schema-lifecycle-best-practices.html).

This maps that guide's four phases + checklist onto **this** pipeline
(Git → `main.py` → Apicurio v3, Debezium-generated Avro + hand-written JSON
Schema log events). Full mechanics: [CLAUDE.md](CLAUDE.md).

## Four phases

| Phase | Registry feature | This repo |
| --- | --- | --- |
| Creation | groups, rules, references | `sync_config` → `sync_bootstrap` → `sync_groups` → `sync_artifacts` (empty artifact before first version) |
| Evolution | compatibility modes | `BACKWARD_TRANSITIVE` global rule (`configs/global_rules.yaml`) rejects breaking changes at registration time |
| Deprecation | version state `DEPRECATED` | Edit `state:` in the table index YAML → CI PUTs it (`core/versions/state.py`); see [CLAUDE.md § Version lifecycle](CLAUDE.md#version-lifecycle-enabled--deprecated--disabled) |
| Retirement | version state `DISABLED`, deletion | `DISABLED` supported the same way; artifact/version **deletion** is intentionally out of scope (Git is the only source of truth — nothing here deletes registry state) |

## Shared types (cross-schema references)

Already implemented: `core/types/shared/catalog.yaml` entries with `register: true`
(e.g. `VariableScaleDecimal`, `Geometry`, `SparseVector`) are registered **once**
into group `debezium` (`core/bootstrap/catalog.py`), and every Key/Value that
uses one gets an Apicurio `references[]` entry instead of a duplicated
definition (`core/versions/mapping.py` → `core/references/`). Also true for the
Debezium `Source` / `event.block` shared types referenced by every Envelope.
No action needed — this already matches "Define shared types as separate
artifacts... reference them from dependent schemas."

## Evolution patterns

Most of the guide's evolution table (add-field-with-default, `["null", type]`
unions, enum symbol removal, type promotion) describes **hand-authored** Avro
evolution. In this pipeline, Key/Value fields are **generated** from Debezium's
own emitted Connect schema (`core/versions/mapping.py`), so:

- New DB columns → new field in a new `vN.yaml` → new artifact **version**.
  Values default every field to nullable (`["null", type]`, `default: null`)
  unless `nullable: false` is set — matches the guide's recommended optional-field
  pattern automatically. Keys default `NOT NULL` (primary keys shouldn't be optional).
- Column type changes are whatever Debezium 3.6.1 emits for the new type — this
  repo does **not** invent a "safer" Avro shape to force compatibility (see
  CLAUDE.md invariant #1). If a change is Avro-incompatible, `BACKWARD_TRANSITIVE`
  will reject the new version at registration — that's the intended guardrail,
  not a bug to work around.
- Avro `aliases:` for field renames: not applicable here — a DB column rename
  is a different column to Debezium, so it lands as a new field in a new
  version, not an in-place rename.
- Protobuf reserved tags: not applicable — this pipeline emits `AVRO`,
  `KCONNECT` (Debezium JSON), and `JSON` (JSON Schema log events); see
  `core/artifacts/artifact_types.py`.

## Data structure recommendations

| Recommendation | Status |
| --- | --- |
| `["null", type]` + `default: null` for optional fields | Automatic for CDC values (`core/versions/mapping.py`) |
| Enums for fixed, closed sets | Used for Debezium's own enums (e.g. `snapshot`), not something table YAML authors choose |
| Nested records for compartmentalized evolution | Follows Debezium's own struct shape (e.g. named catalog types are their own artifact) |

## Checklist

| Do | Status |
| --- | --- |
| Add fields with default values | Automatic (nullable-by-default values) |
| Use `["null", "type"]` for optional fields | Automatic |
| Shared types as separate artifacts | Done (`register: true` catalog + bootstrap refs) |
| Deprecate before disabling | Supported — bump `state:` to `DEPRECATED` first (`docs/CLAUDE.md`) |
| `BACKWARD_TRANSITIVE` for production | Set in `configs/global_rules.yaml` |
| Test schema changes against compatibility rules | Enforced server-side by the global rule at registration; no offline dry-run tool yet |
| Reserve removed Protobuf tags | N/A — no Protobuf artifacts |

| Avoid | Status |
| --- | --- |
| Required fields without defaults | N/A — values are generated nullable by default |
| Removing enum symbols | N/A — enums are Debezium-defined, not user-edited |
| Duplicating type definitions | Avoided via shared catalog references |
| Disabling without warning | Workflow requires `DEPRECATED` as a YAML edit before `DISABLED` (not enforced by code — reviewer discipline) |
| `NONE` compatibility in production | Global rule is `BACKWARD_TRANSITIVE`, never `NONE` |

## Gaps / not enforced by code

- Nothing stops someone from setting `state: DISABLED` directly without ever
  setting `DEPRECATED` first — this is a **review** discipline, not a `main.py`
  check. Could add a lint step later that flags `ENABLED → DISABLED` diffs in
  a table index without a prior `DEPRECATED` commit.
- No automated "test this change against compatibility rules before merging"
  step (e.g. a dry-run against the registry in CI before the register job).
  Currently the register job itself is the compatibility check.
