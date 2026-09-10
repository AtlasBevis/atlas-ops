# Schemas

Git is the source of truth for Avro CDC schemas (Debezium 3.6.1 → Apicurio Registry v3).
CI creates missing groups / artifacts / versions. It does not overwrite existing versions.

| Doc | |
| --- | --- |
| Agent handoff | [docs/CLAUDE.md](docs/CLAUDE.md) |
| Pointer | [CLAUDE.md](CLAUDE.md) |
| Avro naming / auto-transform | [docs/avro-naming.md](docs/avro-naming.md) |
| DB type → Avro | [core/types/README.md](core/types/README.md) |
| Global rules | [core/configs/README.md](core/configs/README.md) |

## Layout

```text
groups/index.yaml                 # catalog of groupIds
groups/<folder>/<table>/
  index.yaml
  keys/vN.yaml
  values/vN.yaml
core/types/                     # Debezium 3.6 mappings + shared catalog
scripts/main.py                 # CI: config → bootstrap → groups → artifacts
```

Folder names need not match `groupId` or `table.name`. Discovery is `groups/*/*/index.yaml`.

## CI flow

1. Sync global rules (`VALIDITY=FULL`, `COMPATIBILITY=BACKWARD`)
2. Bootstrap group `debezium` (Source, `event.block`, named catalog types, …)
3. Create missing groups from `groups/index.yaml`
4. Per table: empty `{topic}-key` / `{namespace}.Value` / `{topic}-value`, then versions `.Value` → `-key` → `-value`
   (`namespace` = `avro_namespace(topic)`; see [docs/avro-naming.md](docs/avro-naming.md))

Job: `.gitlab-ci.yaml` (`cd scripts && python main.py`, env `REGISTRY_URL`).

## References

- [Apicurio Registry v3 API](https://www.apicur.io/registry/docs/apicurio-registry/3.1.x/assets-attachments/registry-rest-api.htm)
- [Debezium 3.6 connectors](https://debezium.io/documentation/reference/3.6/connectors/oracle.html)
