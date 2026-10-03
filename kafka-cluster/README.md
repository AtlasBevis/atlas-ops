# Kafka Cluster

Helm chart deploy **Kafka cluster** (KRaft, 3 controllers + 3 brokers).

## Prerequisites

1. **Strimzi operator** has deployed
2. **StorageClass** `longhorn`

## AUTHENTICATION and AUTHORIZATION

SCRAM (Challenge-Response Authentication)

1. Client → Broker: Send username.
2. Broker → Client: Return salt, nonce, and iteration count.
3. Client: Generate a proof using password + salt + nonce (HMAC-SHA-512).
4. Client → Broker: Send the proof (not the password).
5. Broker: Verify the proof and authenticate the client.

| TLS   | Authentication    | Client Protocol   | Description                                   |
|-------|-------------------|-------------------|-----------------------------------------------|
| false | None              | `PLAINTEXT`       | No encryption, no authentication              |
| false | `scram-sha-512`   | `SASL_PLAINTEXT`  | SCRAM authentication, no TLS                  |
| true  | None              | `SSL`             | TLS encryption, no client authentication      |
| true  | `scram-sha-512`   | `SASL_SSL`        | **PRODUCTION** SCRAM authentication over TLS  |
| true  | `tls`             | `SSL` (mTLS)      | Mutual TLS (client certificate authentication)|
| true  | `oauth`           | `SASL_SSL`        | OAuth authentication over TLS                 |
| true  | `custom`          | Depends           | Custom authentication plugin                  |


## Kafka Node Pool

045-Crd-kafkanodepool.yaml
 - only 2 role (controller | broker)
 - storage: type (ephemeral | persistent-claim | jbod)

## External access (one hostname per broker, shared port 9094)

Kafka is a binary TCP protocol and a client reconnects **straight to the
partition leader**, so `HTTPRoute` / L7 ingress cannot carry it. Every broker
needs its own endpoint.

Each broker gets its **own hostname**, so the TLS SNI distinguishes them and a
single port is enough. The `external` listener in `values.yaml` uses
`type: cluster-ip` (the type Strimzi documents for custom access mechanisms: one
ClusterIP Service per broker pod, no route object):

| Client connects to | Service |
|---|---|
| `broker-3.kafka.example.local:9094` | `kafka-cluster-kafka-external-3:9094` |
| `broker-4.kafka.example.local:9094` | `kafka-cluster-kafka-external-4:9094` |
| `broker-5.kafka.example.local:9094` | `kafka-cluster-kafka-external-5:9094` |

There is **no bootstrap hostname**: clients list all three names as
`bootstrap.servers`. Kafka has no special bootstrap broker — any broker answers
metadata requests. Listing all three matters: a single entry pointing at a broker
that happens to be restarting leaves the client unable to reach the cluster.

All names resolve to the **same** VIP. `advertisedHost` is the address a broker
hands back to the client; `advertisedPort` is omitted because it defaults to the
listener port (9094), shared by every broker. Hosts are listed per node ID under
`configuration.brokers[]` rather than via `advertisedHostTemplate`, so only the
broker pool can ever be advertised — controllers (node IDs 0-2) stay internal.

Strimzi adds the advertised hosts to the broker certificates, so TLS hostname
verification passes without touching the cluster CA.

`gateway-api/values.yaml` holds **one** `Gateway` listener (`kafka-tls`,
`mode: Passthrough`, no `hostname`) plus three `TLSRoute`s selected by hostname.
The L4 proxy in front of the VIP forwards TCP **9094 only**, as passthrough — no
TLS termination, no HTTP. Adding a broker costs one DNS record plus one route; a
wildcard record removes the DNS step.

### Alternative: one hostname, a port per broker

Commented out in `values.yaml` as ALTERNATIVE 1. Sharing a hostname makes the SNI
identical on every connection, so the Gateway has to tell endpoints apart by port.

| | N hostnames, 1 port (active) | 1 hostname, N ports (commented) |
|---|---|---|
| Endpoints told apart by | TLS SNI | listener port |
| Kafka listener config | `advertisedHost` per broker | `advertisedPort` per broker |
| Gateway listeners | 1 (no `hostname`) | 4 |
| DNS records | one per broker | 1 |
| Ports on the L4 proxy | `9094` only | `9094` + `19093-19095` |
| `bootstrap.servers` | all three broker names | the single hostname |
| Cost of adding a broker | one DNS record + route | listener + route + **a new proxy port** |

Corporate proxies usually restrict ports harder than DNS, which is why the active
setup is the N-hostname one: it scales without going back to the network team.
Switch to the commented variant only if DNS is the bottleneck instead. Note the
port variant also couples two files with no validation — a Gateway listener port
that drifts from `advertisedPort` fails only at produce time, after bootstrap
already succeeded.

ALTERNATIVE 2 keeps a hostname per endpoint but adds a bootstrap address and lets
the operator own the routes: `type: tlsroute` with `hostTemplate` means a new
broker needs no chart edit at all, and clients need only one bootstrap entry. It
costs one extra DNS record, because `bootstrap.host` is mandatory for that type.
It also needs Strimzi **>= 1.1.0** — the operator bundled in
`kafka-system/helm/strimzi` is 1.0.1, whose Kafka CRD has no `tlsroute` type and
whose cluster operator ClusterRole has no `tlsroutes` RBAC. Stay on `cluster-ip`
plus hand-written TLSRoutes until that chart is upgraded.

Client config (external) — list every broker, since there is no bootstrap name:

```properties
bootstrap.servers=broker-3.kafka.example.local:9094,broker-4.kafka.example.local:9094,broker-5.kafka.example.local:9094
security.protocol=SASL_SSL
sasl.mechanism=SCRAM-SHA-512
sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required username="<user>" password="<secret>";
ssl.truststore.type=PEM
ssl.truststore.certificates=<ca.crt from secret kafka-cluster-cluster-ca-cert>
```

```bash
# Advertised address each broker returns — must be the public one
kubectl exec -n kafka-system kafka-cluster-brokers-3 -c kafka -- \
  grep -h 'advertised.listeners' /tmp/strimzi.properties

kubectl get svc -n kafka-system | grep kafka-external
kubectl get tlsroute -n kafka-system -o wide     # 3 routes, Accepted=True
```


## Kafka Topic

| Key | required | Default | description |
|-----|----------|---------|-------|
| `name` | x  | — | K8s resource name |
| `topicName` | x | — | topic name|
| `partitions` | | `3` | num partitions (just increse after created) |
| `replicas` | | `3` | Replication factor |
| `config` | | — | Kafka topic config |

some configs often use

| Key | example | description |
|-----|-------|-------|
| `retention.ms` | `604800000` | time keep message (ms) |
| `max.message.bytes` | `1048576` | max message size |

## Kafka Exporter 
Kafka Exporter provides only metrics related to consumer groups and lag.


## Setting up Prometheus

## Document

- [Prometheus](https://strimzi.io/docs/operators/latest/deploying#assembly-metrics-prometheus-str)
- [KafkaTopic Config](https://kafka.apache.org/43/configuration/topic-configs/)
- [Strimzi Kafka CR](https://strimzi.io/docs/operators/latest/configuring.html#type-Kafka-reference)
- [KafkaNodePool](https://strimzi.io/docs/operators/latest/configuring.html#type-KafkaNodePool-reference)
- [Apache Kafka](https://kafka.apache.org/43/configuration/broker-configs/)
