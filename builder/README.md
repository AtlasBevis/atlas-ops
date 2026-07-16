# Builder toolkit

Internal BuildKit daemon for CI/CD image builds with registry-based cache.

## Helm install

```sh
helm upgrade --install builder ./helm \
  --namespace ci --create-namespace \
  --set registry.host=registry.internal:5000 \
  --set registry.http=true \
  --set registry.credentialsSecret=dockerhub-secret
```

Create registry credentials secret (if not exists):

```sh
kubectl create secret docker-registry dockerhub-secret \
  --docker-server=registry.internal:5000 \
  --docker-username=<user> \
  --docker-password=<pass> \
  -n ci
```

## Use from CI

```sh
export BUILDKIT_HOST=tcp://builder.ci.svc:1234

buildctl build \
  --frontend dockerfile.v0 \
  --local context=. \
  --local dockerfile=. \
  --import-cache type=registry,ref=registry.internal/myapp:cache \
  --export-cache type=registry,ref=registry.internal/myapp:cache,mode=max \
  --output type=image,name=registry.internal/myapp:latest,push=true
```

## Docker (local test)

```sh
docker run -d \
  --name buildkitd \
  --privileged \
  -p 1234:1234 \
  moby/buildkit:v0.30.0 \
  --addr tcp://0.0.0.0:1234
```

## References

- [BuildKit](https://github.com/moby/buildkit/)
