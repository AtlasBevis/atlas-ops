# Kafka Connect Cluster

- Kafka Connect is an integration toolkit
- Provides a framework for integrating Kafka with an external data source or target
- Connectors are plugins that provide the connection configuration needed.
- Kafka Connect clusters deployed using the `KafkaConnect` resource
- Connectors created using the `KafkaConnector` resource.

## 1. Kafka Connect

references:

- [Strimzi Provider](https://strimzi.io/docs/operators/latest/full/deploying.html#assembly-loading-config-with-providers-str)
- [Config Provider](https://kafka.apache.org/41/configuration/configuration-providers/)
- [Restart](https://github.com/strimzi/strimzi-kafka-operator/blob/main/documentation/modules/configuring/proc-manual-restart-connector.adoc)

## 2. Kafka Connector

connector.class:
- s3/minio: **io.confluent.connect.s3.S3SinkConnector**
- postgres: **io.debezium.connector.postgresql.PostgresConnector**
- oracle: **io.debezium.connector.oracle.OracleConnector**
- mssql: **io.debezium.connector.sqlserver.SqlServerConnector**
- mysql: **io.debezium.connector.mysql.MySqlConnector**

config explain:

1. `state`: The state the connector should be in. (paused | stopped | running)

2. `annotation`: refer docs: https://strimzi.io/docs/operators/latest/deploying.html#proc-resetting-connector-offsets-str
 
should be run once
```shell
kubectl annotate KafkaConnector <kafka_connector_name> strimzi.io/restart="true"
```

NOTE: stops the connector before resetting offsets.
```yaml
annotations:
  strimzi.io/connector-offsets: reset
```

3. `autoRestart`: the automatic restart to each failed connector and its tasks
```yaml
autoRestart:
  enabled: true
  maxRestarts: 10
```

### 2.1 S3/Minio

docs: https://www.confluent.io/hub/confluentinc/kafka-connect-s3

---
Partitioning
- DefaultPartitioner: Creates a structure based on topic and partition
- FieldPartitioner: Partitions data based on field values from records
- TimeBasedPartitioner: Creates partitions based on record timestamps

To use time-based partitioning:
```sh
partitioner.class: io.confluent.connect.storage.partitioner.TimeBasedPartitioner
path.format: 'year=YYYY/month=MM/day=dd/hour=HH'
timestamp.extractor: RecordField
timestamp.field: timestamp
```

DataFormat and Compression
- JSON: **io.confluent.connect.s3.format.json.JsonFormat**
- Avro: **io.confluent.connect.s3.format.avro.AvroFormat**
- Parquet: **io.confluent.connect.s3.format.parquet.ParquetFormat**

config example:
```yaml
name: s3-sink
enabled: true
class: io.confluent.connect.s3.S3SinkConnector
tasksMax: 10
autoRestart:
enabled: true
maxRestarts: 10
config:
topics.dir: cdc
topics.regex: ^cdc\..*
s3.bucket.name: dp-prod-raw
s3.part.size: '5242880'
aws.access.key.id: ${env:S3_ACCESS_KEY}
aws.secret.access.key: ${env:S3_SECRET_KEY}
store.url: ${env:S3_ENDPOINT}
flush.size: "5"
rotate.interval.ms: "30000" # 5min
storage.class: io.confluent.connect.s3.storage.S3Storage
format.class: io.confluent.connect.s3.format.json.JsonFormat
partitioner.class: io.confluent.connect.storage.partitioner.TimeBasedPartitioner
partition.duration.ms: "3600000"
path.format: "YYYY-MM-dd/HH"
locale: "en-US"
timezone: "Asia/Ho_Chi_Minh"
timestamp.extractor: Record
timestamp.field: ts_ms
behavior.on.null.values: ignore
errors.tolerance: none
```

Best practices:
1. Sizing: Set appropriate `flush.size` based on your record size and frequency
2. Partitioning: Choose a partitioning strategy that aligns with your query patterns
3. Use Parquet or Avro for analytical workloads to improve query performance


### 2.2 Debizum

docs: https://debezium.io/documentation/reference/3.5/connectors/index.html

---
Procedure:
1. Download the Debezium
2. Extract the files into your Kafka Connect environment.
3. Add the directory with the JAR files to Kafka Connect's plugin.path.
4. Restart your Kafka Connect process to pick up the new JAR files.

Oracle config example: 
```yaml
class: io.debezium.connector.oracle.OracleConnector
database.hostname: {env:ORA_HOST}
database.port: 1521
database.user: {env:ORA_USER}
database.password: {env:ORA_PASSWORD}
database.dbname: {env:ORA_DBNAME}
database.pdb.name: ORCLPDB1
topic.prefix: oracle-server1
schema.include.list: MYSCHEMA
table.include.list: MYSCHEMA.CUSTOMERS,MYSCHEMA.ORDERS
database.connection.adapter: logminer
log.mining.strategy: online_catalog
tombstones.on.delete: false
snapshot.mode: initial
include.schema.changes: true
```
Deployments:
- [Oracle](https://debezium.io/documentation/reference/3.5/connectors/oracle.html#oracle-deploying-a-connector)
- [MySQL](https://debezium.io/documentation/reference/3.5/connectors/mysql.html#mysql-deploying-a-connector)
- [Postgres](https://debezium.io/documentation/reference/3.5/connectors/postgresql.html#postgresql-deployment)
- [MSSQL](https://debezium.io/documentation/reference/3.5/connectors/sqlserver.html#sqlserver-deploying-a-connector)
- [Jdbc](https://debezium.io/documentation/reference/stable/connectors/jdbc.html#jdbc-connector-configuration)

Driver if you use Jdbc connector:
- [Oracle](https://www.oracle.com/database/technologies/appdev/jdbc-downloads.html)
- [Postgres](https://jdbc.postgresql.org/download/)
- [MySQL Platform independent](https://dev.mysql.com/downloads/connector/j/)
- [MSSQL](https://learn.microsoft.com/en-us/sql/connect/jdbc/download-microsoft-jdbc-driver-for-sql-server?view=sql-server-ver17#download)

Summary:
| DB | Maven artifact | URL Connection |
| ---| ---------------| ---------------|
| Oracle | `com.oracle.database.jdbc:ojdbc11` | `jdbc:oracle:thin:@//host:1521/service` |
| Postgres | `org.postgresql:postgresql`  | `jdbc:postgresql://host:5432/db` |
| MySQL | `com.mysql:mysql-connector-j` | `jdbc:mysql://host:3306/db` |
| SQL Server | `com.microsoft.sqlserver:mssql-jdbc` | `jdbc:sqlserver://host:1433;databaseName=db` |

## Document

- [Deploying Kafka Connect](https://strimzi.io/docs/operators/latest/deploying#kafka-connect-str)
- [Exposing API](https://strimzi.io/docs/operators/latest/deploying#con-exposing-kafka-connect-api-str)
- [Debezium Connector](https://debezium.io/documentation/reference/3.5/connectors/index.html)
