{{/*
Expand the name of the chart.
*/}}
{{- define "sr.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
  define image registry
*/}}
{{- define "sr.imageRegistry" -}}
{{- coalesce .Values.imageRegistry .Values.global.imageRegistry "quay.io" -}}
{{- end -}}

{{- define "sr.imageRepository" -}}
{{- coalesce .Values.imageRepository .Values.global.imageRepository "apicurio" -}}
{{- end -}}

{{- define "sr.imagePullSecrets" -}}
{{- $local := .Values.imagePullSecrets -}}
{{- $global := .Values.global.imagePullSecrets -}}
{{- if $local }}{{ toYaml $local }}{{ else if $global }}{{ toYaml $global }}{{ end -}}
{{- end -}}

{{- define "sr.imagePullPolicy" -}}
{{- coalesce .Values.imagePullPolicy .Values.global.imagePullPolicy "IfNotPresent" -}}
{{- end -}}

{{- define "sr.imageTag" -}}
{{- coalesce .tag .Values.global.imageTag .Chart.AppVersion -}}
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

{{- define "sr.image" -}}
  {{- if .Values.image }}
    {{- $repository := .Values.image.repository | default "" -}}
    {{- $tag := .Values.image.tag | default "" -}}
    {{- $digest := .Values.image.digest | default "" -}}
    {{- if $digest }}
      {{- printf "%s@%s" $repository $digest -}}
    {{- else }}
      {{- printf "%s:%s" $repository $tag -}}
    {{- end }}
  {{- end }}
{{- end }}
