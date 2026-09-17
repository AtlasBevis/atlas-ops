# Envoy Gateway (VietCredit)

Upstream: **Envoy Gateway v1.9.0** — chỉ giữ chart **`gateway-helm`**.

CRDs (Gateway API + Envoy) đi kèm qua subchart `gateway-helm/charts/crds` khi `crds.enabled: true` (prod). Không dùng `gateway-crds-helm` trong repo này.

Control plane Service: **ClusterIP**. VIP MetalLB gắn data plane (`EnvoyProxy` → Gateway Service `LoadBalancer`).

## Images cần mirror lên private registry

| Upstream | Private (`dockerhub.vietcredit.com.vn`) |
|----------|----------------------------------------|
| `docker.io/envoyproxy/gateway:v1.9.0` | `dockerhub.vietcredit.com.vn/dwh/gateway:v1.9.0` |
| `docker.io/envoyproxy/ratelimit:17b1956c` | `dockerhub.vietcredit.com.vn/dwh/gateway:ratelimit` |
| `docker.io/envoyproxy/envoy:distroless-v1.39.0` | `dockerhub.vietcredit.com.vn/dwh/gateway:proxy` |

```sh
docker pull docker.io/envoyproxy/gateway:v1.9.0
docker pull docker.io/envoyproxy/ratelimit:17b1956c
docker pull docker.io/envoyproxy/envoy:distroless-v1.39.0

REG=dockerhub.vietcredit.com.vn/dwh/gateway
docker tag docker.io/envoyproxy/gateway:v1.9.0           $REG:v1.9.0
docker tag docker.io/envoyproxy/ratelimit:17b1956c       $REG:ratelimit
docker tag docker.io/envoyproxy/envoy:distroless-v1.39.0 $REG:proxy

docker push $REG:v1.9.0
docker push $REG:ratelimit
docker push $REG:proxy
```

Nếu registry không nhận manifest list, dùng `docker buildx imagetools create --tag ...`.

Namespace cần secret `dockerhub-regcred`.

## Pull chart upstream (nâng version)

```sh
helm pull oci://docker.io/envoyproxy/gateway-helm --version v1.9.0 --untar
```

Nếu cụm **đã có CRD** rồi: set `crds.enabled: false` trong values (tránh overwrite). Cụm mới / chưa có CRD: giữ `true`.

## Prod values (tóm tắt)

`gateway-helm/values-prod.yaml`:

- Private images + `imagePullSecrets: dockerhub-regcred`
- `crds.enabled: true`
- `GatewayClass` `eg` + `EnvoyProxy` `eg-proxy-config`, `loadBalancerIP: 172.27.7.22`
- Topology spread soft theo `hostname`

VIP phải free trước sync (xóa `echo-lb` nếu đang giữ IP).

## Smoke test

```sh
kubectl apply -f gateway-helm/examples/smoke-gateway.yaml
curl -H "Host: echo.eg.local" http://172.27.7.22/
kubectl delete -f gateway-helm/examples/smoke-gateway.yaml
```

## References

- [Envoy Gateway Helm](https://gateway.envoyproxy.io/docs/install/install-helm/)
- [Compatibility matrix](https://gateway.envoyproxy.io/news/releases/matrix/)
- [GitHub](https://github.com/envoyproxy/gateway)
