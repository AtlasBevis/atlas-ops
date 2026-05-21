# Argo CD (Helm)

This repository uses helm-chart version `3.4.2`

images should be pull from dockerhub official and push to your private docker registry
we just change images below

--- `argocd`

```yaml
global:
  repository: quay.io/argoproj/argocd
    tag: "3.4.2"
```

--- `redis`

```yaml
redis:
  image:
    repository: ecr-public.aws.com/docker/library/redis
    tag: 8.2.3-alpine
```

## Install helm repository

at `cicd` root folder

```sh

helm upgrade --install argocd infras/argocd \
  -n argocd \
  --create-namespace \
  -f infras/argocd/values-prod.yaml
```

## Document

- [Argo CD operator manual](https://argo-cd.readthedocs.io/en/stable/operator-manual/)
- [Chart argo-cd (argo-helm)](https://github.com/argoproj/argo-helm/tree/main/charts/argo-cd)
