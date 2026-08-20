# Postgres 

We use charts `cnpg/cloudnative-pg` for operator

The chart installs only the operator (controller manager, webhooks, RBAC and CRDs). To provision a PostgreSQL
`Cluster` resource, use the companion [`cluster`](https://github.com/cloudnative-pg/charts/tree/main/charts/cluster) chart
(see the [Cluster chart README](https://github.com/cloudnative-pg/charts/blob/main/charts/cluster/README.md) for details)
or apply your own `Cluster` manifest.

Getting Started
---------------

### Add the chart repository

```sh
helm repo add cnpg https://cloudnative-pg.github.io/charts
helm repo update cnpg
```

### Pull chart

```sh
helm pull cnpg/cloudnative-pg --version 0.29.0 --untar
```


### Images

```sh
docker pull ghcr.io/cloudnative-pg/cloudnative-pg:1.30.0
```


### Document

- [Github](https://github.com/cloudnative-pg/charts)
- [Docs](https://cloudnative-pg.io/docs/1.30/)
- [Home](https://cloudnative-pg.io/)
- [Charts](https://cloudnative-pg.io/charts/)