# Schema Registry (Apicurio)

## Document

- [Blog GitOps](https://www.apicur.io/blog/2026/06/19/registry-gitops)
- [GitOps example repo](https://github.com/Apicurio/apicurio-registry-gitops-example)
- [Apicurio Registry](https://www.apicur.io/registry/)
- [Operator install](https://github.com/Apicurio/apicurio-registry/tree/main/operator/install)
- [Deploying with Operator](https://www.apicur.io/registry/docs/apicurio-registry/3.3.x/getting-started/assembly-deploying-registry-operator.html)
- [GitOps storage README](https://github.com/Apicurio/apicurio-registry/blob/main/app/src/main/java/io/apicurio/registry/storage/impl/gitops/README.md)

## Storage types

Set `registry.registry.storage.type` in `values.yaml`:

| type | use case |
|------|----------|
| `gitops` | Schemas in Git (read-only, recommended for GitOps) |
| `postgresql` / `mysql` | SQL database |
| `kafkasql` | Kafka journal storage |
| `kubernetesops` | Read-only from ConfigMaps |

## Deploy

```bash
helm dependency build
helm upgrade --install schema-registry . -n kafka -f values.yaml
```

## Verify GitOps

```bash
kubectl port-forward -n kafka svc/apicurio-registry-app-service 8080:8080
curl http://localhost:8080/apis/registry/v3/groups
curl http://localhost:8080/apis/registry/v3/admin/gitops/status
```
