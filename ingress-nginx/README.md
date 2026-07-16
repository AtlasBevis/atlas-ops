# Ingress-Nginx Controller

## Image

1. Controller Image

```docker
docker pull registry.k8s.io/ingress-nginx/controller:v1.15.1@sha256:594ceea76b01c592858f803f9ff4d2cb40542cae2060410b2c95f75907d659e1
```

2. Patch Image

```docker
docker pull registry.k8s.io/ingress-nginx/kube-webhook-certgen:v1.6.9@sha256:01038e7de14b78d702d2849c3aad72fd25903c4765af63cf16aa3398f5d5f2dd
```

if using priavte registry

```docker
docker tag \
    registry.k8s.io/ingress-nginx/controller:v1.15.1@sha256:594ceea76b01c592858f803f9ff4d2cb40542cae2060410b2c95f75907d659e1 \
    dockerhub.company.com.vn/nginx/ingress-nginx:v1.15.1
```

### Config

Global configuration passed to the ConfigMap consumed by the controller. Values may contain Helm templates.

docs: https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/configmap/

example:

```yaml
config:
    use-http2: "true"
    annotation-risk-level: Medium
```

### Document

- [Home](https://kubernetes.github.io/ingress-nginx/)
- [Github](https://github.com/kubernetes/ingress-nginx)