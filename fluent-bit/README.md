# Fluent-bit

## Installment Helm

1. add repository
```sh
helm repo add fluent https://fluent.github.io/helm-charts
helm repo update
```

2. search and download repository
```sh
helm search repo fluent
helm pull fluent/fluent-bit --version 0.58.0
```

## Images

```sh
docker pull cr.fluentbit.io/fluent/fluent-bit:5.1.0
```

## References

- [Home](https://fluentbit.io/)
- [Github](https://github.com/fluent/helm-charts)