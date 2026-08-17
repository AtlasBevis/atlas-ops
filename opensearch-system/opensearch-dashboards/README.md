# OpenSearch Dashboards


## Images

```sh
docker pull opensearchproject/opensearch-dashboards:3.7.0
```

## Secrets

opensearch-auth

```sh
kubectl -n opensearch create secret generic opensearch-auth \
  --from-literal=username=admin \
  --from-literal=password="$(openssl rand -base64 32)" \
  --from-literal=cookie="$(openssl rand -base64 32)"
```


## Refereces
