# Schemas

Git is the source of truth for Debezium CDC schemas (Avro or JSON/KCONNECT)
and application JSON Schema events (Debezium 3.6.1 → Apicurio Registry v3).
CI creates missing groups / artifacts / versions. It does not overwrite existing versions.

| Doc | |
| --- | --- |
| Agent handoff | [docs/CLAUDE.md](docs/CLAUDE.md) |
| Pointer | [CLAUDE.md](CLAUDE.md) |
| Avro naming / auto-transform | [docs/avro-naming.md](docs/avro-naming.md) |
| DB type → Avro | [core/types/README.md](core/types/README.md) |
| Global rules | [configs/README.md](configs/README.md) |
| Schema lifecycle best practices | [docs/schema-lifecycle.md](docs/schema-lifecycle.md) |

## Layout

```text
domain/index.yaml                 # catalog of groupIds
domain/<folder>/<table>/
  index.yaml
  keys/vN.yaml
  values/vN.yaml
main.py                         # CI: config → bootstrap → groups → artifacts
configs/                       # Registry global-rules configuration
core/                          # Python package + DB type mappings
```

Folder names need not match `groupId` or `table.name`. Discovery is `domain/*/*/index.yaml`.

## CI flow

1. Sync global rules (`VALIDITY=FULL`, `COMPATIBILITY=BACKWARD_TRANSITIVE`)
2. Bootstrap group `debezium` (Source, `event.block`, named catalog types, …)
3. Create missing groups from `domain/index.yaml`
4. Per table: create empty artifacts, then versions. Avro order is
   `.Value` → `-key` → `-value`; Debezium JSON/KCONNECT and log JSON use
   `-value` → `-key`.

Job: `.gitlab-ci.yml` (`python main.py`, env `REGISTRY_URL`).

## References

- [Apicurio Registry v3 API](https://www.apicur.io/registry/docs/apicurio-registry/3.1.x/assets-attachments/registry-rest-api.htm)
- [Debezium 3.6 connectors](https://debezium.io/documentation/reference/3.6/connectors/oracle.html)
