# Postgres Helm

We use charts `cnpg/cloudnative-pg` for operator and `cnpg/cluster` for PostgreSQL cluster.

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
helm pull cnpg/cluster --version 0.8.1 --untar
```

### Images


```sh
# Operator
docker pull ghcr.io/cloudnative-pg/cloudnative-pg:1.30.0

# Postgres
docker pull ghcr.io/cloudnative-pg/postgresql:16
```

### Postgres Operator

1. Opeartor configuration

[`configuration`](https://cloudnative-pg.io/docs/devel/operator_conf/)

### Document

- [Github](https://github.com/cloudnative-pg/charts)
- [Docs](https://cloudnative-pg.io/docs/1.30/)
- [Home](https://cloudnative-pg.io/)
- [Charts](https://cloudnative-pg.io/charts/)