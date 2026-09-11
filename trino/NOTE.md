# Trino Helm (1.42.2)

## Installment

1. Add the Trino Helm chart

```sh
helm repo add trino https://trinodb.github.io/charts
```

2. Update repo 

```sh
helm repo update
```

3. Pull chart

```sh
helm pull trino/trinoo --version 1.42.2 --untar
```

## Images


### References

- [Installation K8s](https://trino.io/docs/current/installation/kubernetes.html#)
- [GitHub](https://github.com/trinodb/trino)
