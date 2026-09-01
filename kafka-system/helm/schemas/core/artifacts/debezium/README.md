# Domain → Debezium connector (Source schema)

Shared types live under `domain/debezium/`. Each **domain Envelope** inlines the Source that matches its connector — never mix Oracle Source into an MSSQL domain (or vice versa).

| Domain group | Connector | Shared Source artifact | Path |
|--------------|-----------|------------------------|------|
| `card-bo` | Oracle | `cdc.card-bo.prod` → `cdc.card_bo.prod.…` | `oracle.source/` |
| `card-bo-uat` | Oracle | `cdc.uat.card-bo` → `cdc.uat.card_bo.…` | `oracle.source/` |
| `card-fe` | Oracle | (same pattern) | `oracle.source/` |
| `lms` | SQL Server | `cdc.lms.…` | `sqlserver.source/` |

| Shared (all connectors) | ArtifactId | Path |
|-------------------------|------------|------|
| Transaction block | `event.block` | `event.block/` |

## Rules

1. **One Source artifact per connector** in group `debezium` — not per domain table.
2. **Domain table** (`card-bo`, `lms`, …) only owns `-key` / `-value` Envelopes; inline the correct Source + `event.block`.
3. Adding a new domain: pick connector from the table above (or add a row + new `*.source/` if connector is new).
4. Before production freeze: `curl` live Registry content and align `.avsc` if Debezium version added fields.

See [docs/schema-model.md](../../docs/schema-model.md) — dùng `python new_table.py` (không copy template tay).
