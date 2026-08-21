# Gateway APIs

### Installment Gateway API K8s

refer docs: [GatewayAPIs](https://gateway-api.sigs.k8s.io/guides/getting-started/introduction/)

```sh
kubectl apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.6.1/standard-install.yaml
```

### Installment Envoy Gateway with Helm

1. Pull chart Envoy Gateway CRDs

```sh
helm pull oci://docker.io/envoyproxy/gateway-crds-helm --version v1.9.0 --untar
```

2. Pull controller
```sh
helm pull oci://docker.io/envoyproxy/gateway-helm --version v1.9.0 --untar
```

### Images

1. pull images if private registry

```sh
# gateway
docker pull docker.io/envoyproxy/gateway:v1.9.0
# ratelimit
docker pull docker.io/envoyproxy/ratelimit:17b1956c
# proxy
docker pull docker.io/envoyproxy/envoy:distroless-v1.39.0
```

### Refereces

- [Github](https://github.com/envoyproxy/gateway)
- [Envoy Gateway](https://gateway.envoyproxy.io/docs/install/install-helm/)
