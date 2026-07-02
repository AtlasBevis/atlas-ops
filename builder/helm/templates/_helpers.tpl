{{/*
Expand the chart name.
*/}}
{{- define "builder.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{/*
Expand the namespace
*/}}
{{- define "builder.namespace" -}}
{{- default .Release.Namespace .Values.namespace -}}
{{- end }}


{{/*
Selector labels
*/}}
{{- define "builder.selectorLabels" -}}
app.kubernetes.io/name: {{ include "builder.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "builder.labels" -}}
helm.sh/chart: {{ include "builder.name" . }}
{{ include "test.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}