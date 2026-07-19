# Schemas GitOps

### File Types

| `$type` | Description |
|---------|-------------|
| `registry-v0` | Registry configuration — global rules, settings, scoped by `registryId` |
| `group-v0` | Group definition, scoped by `registryIds` |
| `artifact-v0` | Artifact with inline versions, scoped by `registryIds` |
| `content-v0` | *(Optional)* Content metadata for explicit `contentId` and references |

### Example Repository Layout

```
my-schemas/
├── config/
│   ├── prod.registry.yaml            # registry-v0: registryId: prod
│   └── staging.registry.yaml         # registry-v0: registryId: staging
├── payments/
│   ├── payments.registry.yaml        # group-v0: registryIds: [prod, staging]
│   ├── order-created.registry.yaml   # artifact-v0: registryIds: [prod, staging]
│   ├── order-created-v1.avsc
│   └── order-created-v2.avsc
└── experimental/
    ├── experimental.registry.yaml    # group-v0: registryIds: [staging]
    ├── user-activity.registry.yaml   # artifact-v0: registryIds: [staging]
    └── user-activity.avsc
```

### Document

- [Schema Debezium](https://github.com/debezium/debezium/blob/main/debezium-connector-binlog/src/main/java/io/debezium/connector/binlog/converters/ZeroDateFallbackConverter.java#L110)

- [Rule Types](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-rule-reference.html)

-[Explain Config](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-configuring-kubernetesops-storage.html)
