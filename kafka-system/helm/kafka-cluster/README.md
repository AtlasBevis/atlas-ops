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
