# Schemas — read this first

Handoff for agents working under `kafka-system/helm/schemas`.

**Full playbook:** [docs/CLAUDE.md](docs/CLAUDE.md)

**Avro naming / auto-transform (`avro_namespace` regex):** [docs/avro-naming.md](docs/avro-naming.md)

Type mapping (Debezium 3.6.1 → Avro): [core/types/README.md](core/types/README.md)

Do not use the old `domain/` / `new_table.py` layout. Git YAML → CI `scripts/main.py` → Apicurio v3.
