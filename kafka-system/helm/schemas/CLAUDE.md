# Schemas — read this first

Handoff for agents working under `dp-schemas`.

**Full playbook:** [docs/CLAUDE.md](docs/CLAUDE.md)

**Schema lifecycle best practices compliance:** [docs/schema-lifecycle.md](docs/schema-lifecycle.md)

**Avro naming / auto-transform (`-` → `_`, artifactIds):** [docs/avro-naming.md](docs/avro-naming.md)

Type mapping (Debezium 3.6.1 → Avro): [core/types/README.md](core/types/README.md)

Source YAML lives in `domain/` (Apicurio groups). Git YAML → CI `python main.py` → Apicurio v3.

CDC (`source.type: debezium`) supports `format: avro` (`artifactType: AVRO`) and
`format: json` (`artifactType: KCONNECT`, the ExtJsonConverter schema format).
An omitted format defaults to `json` in
`core/artifacts/artifact_types.py`. Log events use JSON Schema
(`artifactType: JSON`, `-key` / `-value` only).
