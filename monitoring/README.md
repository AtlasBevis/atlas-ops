# Monitoring

We are using `kube-prometheus-stack` to manage on-prem k8s cluster

## Installment Helm

1 add repository

```sh
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```
2. Pull chart

```sh
helm pull prometheus-community/kube-prometheus-stack --version 88.5.0 --untar
```

## References

- [CRD API Refereces](https://prometheus-operator.dev/docs/api-reference/api/)
- [Kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [Helm chart](https://artifacthub.io/packages/helm/prometheus-community/kube-prometheus-stack)
- [Prometheus.io](https://prometheus.io/)
- [Github](https://github.com/prometheus/prometheus)