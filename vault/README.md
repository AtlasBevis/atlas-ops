# HashiCorp Vault (Helm)

```sh
helm repo add hashicorp https://helm.releases.hashicorp.com

helm repo update

helm upgrade --install vault hashicorp/vault \
-n vault \
--create-namespace
-f infras/vault/values-prod.yaml \
```


## Init and unseal

## Document

- [Vault trên Kubernetes](https://developer.hashicorp.com/vault/docs/platform/k8s)
- [vault-helm GitHub](https://github.com/hashicorp/vault-helm)
