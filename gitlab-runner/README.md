# Gitlab Runner

- Chart version: `0.90.1`
- Gitlab runner version: `19.1.1`

## Images

Choose 1 image for gitlab-runner 

```docker
# alpine
docker pull registry.gitlab.com/gitlab-org/gitlab-runner:alpine-v19.1.1

# ubuntu
docker pull registry.gitlab.com/gitlab-org/gitlab-runner:ubuntu-v19.1.1
```

For the `kubernetes`, `docker` executor, need to helper for clone source, upload/download, artifacts, cache...

```docker
docker pull registry.gitlab.com/gitlab-org/gitlab-runner/gitlab-runner-helper:x86_64-v19.1.1
```

## Should



## Document

- [Install K8s](https://docs.gitlab.com/runner/install/kubernetes/)
- [Docs](https://docs.gitlab.com/runner/)
- [Charts](https://gitlab.com/gitlab-org/charts/gitlab-runner)
- [Repository](https://gitlab.com/gitlab-org/gitlab-runner)
