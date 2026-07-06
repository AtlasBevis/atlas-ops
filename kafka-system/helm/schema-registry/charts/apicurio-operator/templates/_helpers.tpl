{{/*
Expand the name of the chart.
*/}}
{{- define "sr.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "sr.image" -}}
{{- printf "%s/%s/%s:%s" .registry .repository .name .tag -}}
{{- end -}}

{{/*
 Selector labels
*/}}
{{- define "sr.selectorLabels" -}}
app: apicurio-registry-operator
app.kubernetes.io/name: {{ include "sr.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
 commons labels
*/}}
{{- define "sr.labels" -}}
{{ include "sr.selectorLabels" . }}
app.kubernetes.io/component: operator
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/part-of: apicurio-registry
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
 Create a list of comma-separated namespaces the operators should watch.
*/}}
{{- define "sr.watchNamespaces" -}}
{{- $namespacesList := .Values.operator.watchNamespaces | default (list) -}}
{{- $returnList := append $namespacesList .Release.Namespace | sortAlpha | uniq -}}
{{- join "," $returnList -}}
{{- end -}}