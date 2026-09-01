## Schemas

Source of truth for Avro schemas

| Doc                 |                                                              |
| ------------------- | ------------------------------------------------------------ |
| Model (5 artifacts) | [docs/schema-model.md](docs/schema-model.md)                 |
| How-to              | [docs/how-to-create-schema.md](docs/how-to-create-schema.md) |
| Domain→connector    | [domain/debezium/README.md](domain/debezium/README.md)       |

## Layout (nhẹ)

```text
groups/groups.registry.yaml
domain/
  debezium/          # event.block + oracle|sqlserver Source
  card-bo/<table>/   # key + record(.Value) + envelope(-value)
scripts/
  main.py            # CI entry
  new_table.py       # CLI codegen
```

## CI flow

1. List/create groups
2. List artifacts + versions
3. Create missing only (debezium → record → key → envelope)

## Rerferences

- [API Specs](https://www.apicur.io/registry/docs/apicurio-registry/3.0.x/assets-attachments/registry-rest-api.htm)
