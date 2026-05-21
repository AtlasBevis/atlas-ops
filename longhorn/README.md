# Longhorn (Helm)

Thư mục này chứa file values cho [Longhorn](https://longhorn.io/) — CSI storage phân tán trên Kubernetes, cung cấp `StorageClass` (mặc định thường là `longhorn`) dùng bởi các workload khác trong repo (ví dụ Vault dùng `storageClass: longhorn`).

## Điều kiện cluster (tóm tắt)

- Cài **open-iscsi** (và dịch vụ `iscsid` chạy) trên **mọi node** sẽ chạy replica/engine.
- Mount helper: `nfs-common` / `nfs-utils` tùy distro (cần cho RWX qua share manager).
- Kiểm tra thêm theo [installation requirements](https://longhorn.io/docs/latest/deploy/install/#installation-requirements) của phiên bản bạn chọn.

## Cài đặt từ Helm repository

Chạy từ thư mục gốc repository `cicd` (để đường dẫn `-f` đúng).

```sh
helm repo add longhorn https://charts.longhorn.io

helm repo update

helm upgrade --install longhorn longhorn/longhorn \
  -n longhorn-system \
  --create-namespace \
  -f infras/longhorn/values.yaml
```

Môi trường dev (ít node, ít replica hơn):

```sh
helm upgrade --install longhorn longhorn/longhorn \
  -n longhorn-system \
  --create-namespace \
  -f infras/longhorn/values.yaml \
  -f infras/longhorn/values-dev.yaml
```

## Tài liệu tham khảo

- [Longhorn — Install với Helm](https://longhorn.io/docs/latest/deploy/install/install-with-helm/)
- [Chart longhorn (charts.longhorn.io)](https://github.com/longhorn/longhorn/tree/master/chart)
