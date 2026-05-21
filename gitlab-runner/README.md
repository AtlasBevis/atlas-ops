# Gitlab-runner (Helm)

This repository uses helm-chart

images should be pull from dockerhub official and push to your private docker registry
we just change images below

--- `runner`

```yaml`
image:
  registry: dockerhub.example.com.vn
  image: gitlab/gitlab-runner
  tag: alpine3.21-36b1f255
```

--- `job`

```yaml
runners:
  config: |
    [[runners]]
      [runners.kubernetes]
        image = "dockerhub.company.com.vn/alpine:3.23"
        image_pull_secrets = ["dockerhub-secret"]
        pull_policy = "if-not-present"
```

## Install helm repository

at `cicd` root folder

```sh

helm upgrade --install argocd infras/gitlab-runner \
  -n gitlab-runner \
  --create-namespace \
  -f infras/gitlab-runner/values-prod.yaml
```
