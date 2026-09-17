# Metal LB

## Images

1. (optional) pull image for private registry

```sh
# controller
docker pull quay.io/metallb/controller:v0.16.1

# speaker
docker pull quay.io/metallb/speaker:v0.16.1
```

Prod VIP pool (`values-prod.yaml`): `172.27.7.22/32` (`autoAssign: false`). Same IP is used by Envoy Gateway data-plane `EnvoyProxy` loadBalancerIP.

## References

- [MetalLB](https://metallb.io/installation/)
