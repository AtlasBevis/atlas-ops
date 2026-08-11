{{/*
Expand the name of the chart.
*/}}
{{- define "connect.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Kafka Connect cluster name used by Strimzi CRs and REST service.
Service: <clusterName>-connect-api.<namespace>.svc:8083
*/}}
{{- define "connect.clusterName" -}}
{{- required "clusterName is required" .Values.clusterName -}}
{{- end -}}

{{/*
Bootstrap servers for the upstream Kafka cluster.
*/}}
{{- define "connect.bootstrapServers" -}}
{{- $kc := .Values.kafka -}}
{{- printf "%s-kafka-bootstrap.%s.svc:%v" (required "kafkaCluster.name is required" $kc.name) (required "kafkaCluster.namespace is required" $kc.namespace) (default 9092 $kc.bootstrapPort) -}}
{{- end -}}

{{/*
Labels for Kafka Connect resources.
*/}}
{{- define "connect.labels" -}}
strimzi.io/cluster: {{ include "connect.clusterName" . }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
app.kubernetes.io/name: {{ include "connect.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}


{{- define "debezium.sourceClass" -}}
{{- $type := required "source.type is required" .sourceTyoe | lower -}}
{{- $classes := dict
  "oracle"    "io.debezium.connector.oracle.OracleConnector"
  "postgres"  "io.debezium.connector.postgresql.PostgresConnector"
  "mysql"     "io.debezium.connector.mysql.MySqlConnector"
  "sqlserver" "io.debezium.connector.sqlserver.SqlServerConnector"
  "mongodb"   "io.debezium.connector.mongodb.MongoDbConnector"
-}}

{{- if not (hasKey $classes $type) -}}
  {{- fail (printf "Unsupported Debezium source.type: %s" $type) -}}
{{- end -}}

{{- get $classes $type -}}
{{- end -}}


{{/*
S3 sink name: <name>-s3-sink
Usage: include "connect.s3.name" .name
*/}}
{{- define "connect.s3.name" -}}
{{- printf "%s-s3-sink" (required "name is required" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
S3 sink connector class
*/}}
{{- define "connect.s3.class" -}}
io.confluent.connect.s3.S3SinkConnector
{{- end -}}

{{/*
Iceberg sink KafkaConnector name: iceberg-<name>
Usage: include "connect.iceberg.name" .
Context: item from .Values.icebergs
*/}}
{{- define "connect.iceberg.name" -}}
{{- printf "iceberg-%s" (required "name is required" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Iceberg sink connector class
*/}}
{{- define "connect.iceberg.class" -}}
org.apache.iceberg.connect.IcebergSinkConnector
{{- end -}}
