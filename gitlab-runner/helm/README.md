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

## Secrets

### 1. Register Runner

runner-token should be empty

```shell
kubectl create secret generic gitlab-runner-secret \
  --from-literal=runner-registration-token="$TOKEN_HERE" \
  --from-literal=runner-token="" \
  -n "gitlab-runner" 
```

### 2. (Optional) Private Docker Registry (recommend using robot account or sa)

```shell
kubectl create secret docker-registry dockerhub-regcred \
    --docker-server='dockerhub.company.com.vn' \
    --docker-username='robot$...' \  
    --docker-password='pass@123' \
    --docker-email='dwh@company.com.vn' \
    -n gitlab-runner
```

### 3. (Optional) SSH Private Repository

3.1 Create Key Pair

```sh
mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
ssh-keygen -t ed25519 -C "gitlab-runner" -f "$HOME/.ssh/id_ed25519" -N ""
chmod 600 "$HOME/.ssh/id_ed25519"
chmod 644 "$HOME/.ssh/id_ed25519.pub"
```

3.2. Get Known_Hosts

```sh
ssh-keyscan -H gitlab.company.com.vn > "$HOME/.ssh/known_hosts"
chmod 644 "$HOME/.ssh/known_hosts"
```

3.3 Create Secrets

```shell
kubectl create secret generic gitlab-runner-ssh \
  --from-file=id_ed25519="$HOME/.ssh/id_ed25519" \
  --from-file=id_ed25519.pub="$HOME/.ssh/id_ed25519.pub" \
  --from-file=known_hosts="$HOME/.ssh/known_hosts" \
  -n gitlab-runner
```

### 4. (Optionnal) Using runners cache (One of: s3, gcs, azure.)

```shell
kubectl create secret generic s3access \
  --from-literal=accesskey='MINIO_ACCESS_KEY' \
  --from-literal=secretkey='MINIO_SECRET_KEY'
  -n gitlab-runner 
```

## Best Practice

### 1. (Optional) Using runner cache (.m2, .npm, .cache/pip, Gradle cache…)

docs: 
- [Section](https://docs.gitlab.com/runner/configuration/advanced-configuration/#the-runnerscache-section)
- [S3](https://docs.gitlab.com/runner/configuration/advanced-configuration/#the-runnerscaches3-section)

```yaml
runners
    cache:
```


## Document

- [Configuration](https://docs.gitlab.com/runner/executors/kubernetes/#configuration-settings)
- [Install K8s](https://docs.gitlab.com/runner/install/kubernetes/)
- [Docs](https://docs.gitlab.com/runner/)
- [Charts](https://gitlab.com/gitlab-org/charts/gitlab-runner)
- [Repository](https://gitlab.com/gitlab-org/gitlab-runner)
