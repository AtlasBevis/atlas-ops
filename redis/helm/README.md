# Redis Helm Chart


## Image

```docker
docker pull registry-1.docker.io
```

## Install 
1. Add repository 

```sh
helm repo add bitnami https://charts.bitnami.com/bitnami
```

2. Install chart

```sh
helm install my-redis bitnami/redis --version 27.0.18
```


## References

- [Chart](https://artifacthub.io/packages/helm/bitnami/redis)
- [Github](https://github.com/bitnami/charts/tree/main/bitnami/redis)