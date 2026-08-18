# Longhorn (Helm)

version: 1.12.0

## Installation Requirements

Each node in the Kubernetes cluster where Longhorn is installed must fullfill the following requirements:
    1. Some tools package need to install
```sh
sudo apt update
sudo apt install -y open-iscsi nfs-common curl gawk util-linux
sudo systemctl enable --now iscsid
sudo systemctl status iscsid
```

> util-linux contains findmnt, blkid; gawk for awk.

## Install Helm

1. Add the respository

```sh
helm repo add longhorn https://charts.longhorn.io
helm repo update
```

2. Install Longhorn in the `longhorn-system` namespace.

```sh
helm install longhorn longhorn/longhorn --namespace longhorn-system --create-namespace --version 1.12.1
```

## Tài liệu tham khảo

- [Install Requirements](https://longhorn.io/docs/1.12.1/deploy/install/#installation-requirements)
- [Chart](http://artifacthub.io/packages/helm/longhorn/longhorn)
- [Longhorn — Install với Helm](https://longhorn.io/docs/latest/deploy/install/install-with-helm/)
- [Chart longhorn (charts.longhorn.io)](https://github.com/longhorn/longhorn/tree/master/chart)
