# Redis Helm Chart


## Image

```docker
docker pull registry-1.docker.io
docker pull registry-1.docker.io/bitnami/kubectl:latest@sha256:1a86ba502f618724fd493f6a2b129f060454db04f06faa58d8ed94510280b17f
docker pull registry-1.docker.io/bitnami/redis-exporter:latest
```

```docker

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