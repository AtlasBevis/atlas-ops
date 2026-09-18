# gateway-api

Helm chart để khai báo tài nguyên **Gateway API** (`Gateway`, `HTTPRoute`,
`GRPCRoute`, `ReferenceGrant`) cho app đứng sau một Gateway API controller
dùng chung (ví dụ Envoy Gateway). Chart này **không** cài controller/CRD —
chỉ tạo các object app cần để lộ ra ngoài qua VIP LoadBalancer.

Toàn bộ cấu hình nằm trong **một file `values.yaml`** — mỗi block đã có ví
dụ comment sẵn, copy/uncomment và đổi tên/host/service là dùng được.

## Vì sao tách chart riêng khỏi chart controller?

- Chart controller (Envoy Gateway, ...): cài Deployment + `GatewayClass` +
  proxy config (ghim VIP). Đổi ít, đổi chậm.
- `gateway-api` (chart này): danh sách route theo host/app. Đổi thường
  xuyên — thêm domain mới không cần đụng chart controller.

Một `Gateway` dùng chung cho toàn bộ VIP; mỗi app chỉ cần thêm một entry
vào `httpRoutes` (hoặc `grpcRoutes`).

## 6 bước chuẩn (xem comment trong `values.yaml`)

1. `gatewayClassName` = tên `GatewayClass` mà controller đã tạo.
2. Điền **đúng một** entry trong `gateways` — Gateway dùng chung claim VIP.
3. `defaultParentRefs` trỏ vào Gateway ở bước 2, để route không phải khai lại `parentRefs`.
4. Thêm route: mỗi host/app một entry trong `httpRoutes` (hoặc `grpcRoutes` cho gRPC).
5. Chỉ thêm `referenceGrants` khi backend Service nằm namespace khác route.
6. Chỉ thêm `sessionAffinity` khi backend có >1 replica **và** giữ state
   theo session (login/OAuth trong memory, SSE/long-poll, cache dính
   session, ...). Backend stateless thì bỏ qua, không cần cookie affinity.
7. `helm lint . && helm template . | less` trước khi apply/sync.

### Case thường gặp

```yaml
httpRoutes:
  - name: example-app
    namespace: example-app
    hostnames:
      - example-app.example.local
    backendRefs:
      - name: example-app-svc
        port: 80
```

Không cần khai `parentRefs` (dùng `defaultParentRefs`), không cần
`path`/`pathType` (mặc định `PathPrefix "/"`).

### Case nâng cao — dùng `rules` thô

Khi cần weighted split, header/query match, filter (redirect, rewrite,
mirror), set `rules` (đúng schema `HTTPRouteRule` upstream) — chart bỏ qua
shorthand và dùng nguyên `rules` đó. Ví dụ trong `values.yaml`.

## Mở rộng gRPC

`grpcRoutes` cùng shape với `httpRoutes`. Hai điều bắt buộc để gRPC chạy
qua gateway:

1. **Service port** của backend phải set `appProtocol: kubernetes.io/h2c`
   (HTTP/2 cleartext) — thiếu thì proxy upstream bằng HTTP/1.1 và gRPC lỗi.
2. Listener trên `Gateway` mà route trỏ vào phải là `HTTP` (h2c) hoặc
   `HTTPS` (h2/TLS).

## ReferenceGrant

Chỉ cần khi `backendRefs`/`certificateRefs` trỏ sang **namespace khác**
với route/Gateway đang tham chiếu. Khai trong namespace **bị tham chiếu
tới** (namespace Service/Secret), không phải namespace route.

## Session affinity (cookie) — thay thế nginx `affinity: cookie`

Khi migrate một app từ nginx-ingress sang chart này, nếu Ingress cũ có
annotation `nginx.ingress.kubernetes.io/affinity: cookie` (thường vì backend
chạy nhiều replica và giữ state trong memory — session login, SSE...), phải
khai lại tương đương bằng `sessionAffinity` trên route đó:

```yaml
httpRoutes:
  - name: example-app
    namespace: example-app
    hostnames:
      - example-app.example.local
    backendRefs:
      - name: example-app-svc
        port: 80
    sessionAffinity:
      cookieName: example-app-affinity
      ttl: 48h   # Max-Age cookie, ví dụ 2 ngày
```

Chart sẽ render một `BackendTrafficPolicy` (`gateway.envoyproxy.io/v1alpha1`,
CRD của Envoy Gateway) `targetRefs` vào đúng `HTTPRoute`/`GRPCRoute` đó, dùng
`loadBalancer.consistentHash.type: Cookie`. Nếu request chưa có cookie, Envoy
tự sinh cookie + trả về `Set-Cookie` (TTL = `ttl`), các request sau cùng
cookie sẽ luôn được route về đúng 1 pod backend — hành vi tương đương nginx.

Bỏ qua field này với backend stateless (không cần sticky routing).

> ⚠️ `ttl` phải đúng format Duration mà CRD validate:
> `^([0-9]{1,5}(h|m|s|ms)){1,4}$` — tối đa **5 chữ số** mỗi đơn vị. Ví dụ
> 2 ngày phải viết `48h`, viết `172800s` (6 chữ số) sẽ bị API server
> reject.

## Cài / test local

```bash
helm lint .
helm template gw . | less

# sau khi apply / sync:
kubectl get gateway -A
kubectl get httproute -A -o wide
kubectl get grpcroute -A -o wide
kubectl describe gateway <name> -n <namespace>   # check .status
```

## References

- [Gateway API docs](https://gateway-api.sigs.k8s.io/)
- [Envoy Gateway — HTTPRoute](https://gateway.envoyproxy.io/docs/tasks/traffic/http-routing/)
- [Envoy Gateway — gRPCRoute](https://gateway.envoyproxy.io/docs/tasks/traffic/grpc-routing/)
