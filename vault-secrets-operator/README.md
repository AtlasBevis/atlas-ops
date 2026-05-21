# Vault System

We use vault-secrets-operator in eco-system Vault

```sh
helm repo add hashicorp https://helm.releases.hashicorp.com

helm repo update

helm install vault-secrets-operator hashicorp/vault-secrets-operator \
  -n vault-system \
  --create-namespace
  --wait
```

## Document

- [Vault Secrets Operator](https://developer.hashicorp.com/vault/docs/platform/k8s/vso)
- [Repository vault-secrets-operator](https://github.com/hashicorp/vault-secrets-operator)
