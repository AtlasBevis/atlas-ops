{{/*
Expand the name of the chart.
*/}}
{{- define "kafka.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Kafka cluster name used by Strimzi CRs and bootstrap service.
*/}}
{{- define "kafka.clusterName" -}}
{{- required "clusterName is required" .Values.clusterName -}}
{{- end -}}

{{/*
KafkaTopic metadata name
*/}}
{{- define "topic.metadataName" -}}
{{- $name := trunc 57 (. | toString) | trimSuffix "-" -}}
{{- printf "%s-topic" $name -}}
{{- end -}}

{{/*
 labels for resources
*/}}
{{- define "kafka.labels" -}}
strimzi.io/cluster: {{ include "kafka.clusterName" . }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
app.kubernetes.io/name: {{ include "kafka.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Kafka Exporter Service name
Usage:
  {{ include "kafkaExporter.name" (dict "clusterName" $clusterName "cfg" $cfg) }}
*/}}
{{- define "kafkaExporter.name" -}}
{{- $root := .root | default . -}}
{{- $cfg := .cfg | default (dict) -}}
{{- $svc := get $cfg "service" | default (dict) -}}
{{- $override := get $svc "name" | default "" -}}
{{- $clusterName := .clusterName | default (include "kafka.clusterName" $root) -}}
{{- $name := default (printf "%s-kafka-exporter" $clusterName) $override -}}
{{- $name | lower | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Return true if PodMonitor CRD is available.
*/}}
{{- define "kafkaExporter.hasPodMonitor" -}}
{{- .Capabilities.APIVersions.Has "monitoring.coreos.com/v1/PodMonitor" -}}
{{- end -}}

{{/*
Return true if ServiceMonitor CRD is available.
*/}}
{{- define "kafkaExporter.hasServiceMonitor" -}}
{{- .Capabilities.APIVersions.Has "monitoring.coreos.com/v1/ServiceMonitor" -}}
{{- end -}}