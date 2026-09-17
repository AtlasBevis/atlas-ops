# Envoy Gateway

Control plane Service: **ClusterIP**. VIP MetalLB gắn data plane (`EnvoyProxy` → Gateway Service `LoadBalancer`).

## Images cần mirror lên private registry

```sh
docker pull docker.io/envoyproxy/gateway:v1.9.0
docker pull docker.io/envoyproxy/ratelimit:17b1956c
docker pull docker.io/envoyproxy/envoy:distroless-v1.39.0
```

## Pull chart

```sh
helm pull oci://docker.io/envoyproxy/gateway-helm --version v1.9.0 --untar
```

Nếu cụm **đã có CRD** rồi: set `crds.enabled: false` trong values (tránh overwrite). Cụm mới / chưa có CRD: giữ `true`.

## References

- [Envoy Gateway Helm](https://gateway.envoyproxy.io/docs/install/install-helm/)
- [Compatibility matrix](https://gateway.envoyproxy.io/news/releases/matrix/)
- [GitHub](https://github.com/envoyproxy/gateway)
