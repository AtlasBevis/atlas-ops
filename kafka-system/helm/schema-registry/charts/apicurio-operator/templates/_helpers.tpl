{{/*
Expand the name of the chart.
*/}}
{{- define "operator.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
  get operator image registry from parent, fallback child
*/}}
{{- define "operator.imageRegistry" -}}
{{- coalesce .Values.imageRegistry .Values.global.imageRegistry "quay.io" -}}
{{- end -}}

{{/*
  get operator image repository from parent, fallback child
*/}}
{{- define "operator.imageRepository" -}}
{{- coalesce .Values.imageRepository .Values.global.imageRepository "apicurio" -}}
{{- end -}}

{{/*
  get operator image pull policy from parent, fallback child
*/}}
{{- define "operator.imagePullPolicy" -}}
{{- coalesce .Values.imagePullPolicy .Values.global.imagePullPolicy "IfNotPresent" -}}
{{- end -}}

{{/*
  get operator image pull secrets from parent, fallback child
*/}}
{{- define "operator.imagePullSecrets" -}}
{{- $secrets := .Values.imagePullSecrets -}}
{{- if $secrets -}}
{{ toYaml $secrets }}
{{- end -}}
{{- end -}}

# ============================
# ========= OPERATOR =========
# ============================
{{/*
  get operator image name from parent, fallback child
*/}}
{{- define "operator.operatorImageName" -}}
{{- $globalName := "" -}}
{{- if and .Values.global.images .Values.global.images.operator -}}
  {{- $globalName = .Values.global.images.operator.name -}}
{{- end -}}
{{- coalesce .Values.operator.image.name $globalName "apicurio-registry-3-operator" -}}
{{- end -}}

{{/*
  get operator image tag from parent, fallback child
*/}}
{{- define "operator.operatorImageTag" -}}
{{- $globalTag := .Values.global.imageTag -}}
{{- if and .Values.global.images .Values.global.images.operator -}}
  {{- $globalTag = .Values.global.images.operator.tag -}}
{{- end -}}
{{- coalesce .Values.operator.image.tag .Values.imageTag $globalTag .Chart.AppVersion -}}
{{- end -}}

# ============================
# ========= APP =============
# ============================
{{/*
  get app image name from parent, fallback child
*/}}
{{- define "operator.appImageName" -}}
{{- $globalName := "" -}}
{{- if and .Values.global.images .Values.global.images.app -}}
  {{- $globalName = .Values.global.images.app.name -}}
{{- end -}}
{{- coalesce .Values.app.image.name $globalName "apicurio-registry" -}}
{{- end -}}

{{/*
  get app image tag from parent, fallback child
*/}}
{{- define "operator.appImageTag" -}}
{{- $globalTag := .Values.global.imageTag -}}
{{- if and .Values.global.images .Values.global.images.app -}}
  {{- $globalTag = .Values.global.images.app.tag -}}
{{- end -}}
{{- coalesce .Values.app.image.tag .Values.imageTag $globalTag .Chart.AppVersion -}}
{{- end -}}

# ============================
# ========= UI =========
# ============================
{{/*
  get ui image name from parent, fallback child
*/}}
{{- define "operator.uiImageName" -}}
{{- $globalName := "" -}}
{{- if and .Values.global.images .Values.global.images.ui -}}
  {{- $globalName = .Values.global.images.ui.name -}}
{{- end -}}
{{- coalesce .Values.ui.image.name $globalName "apicurio-registry-ui" -}}
{{- end -}}

{{/*
  get ui image tag from parent, fallback child
*/}}
{{- define "operator.uiImageTag" -}}
{{- $globalTag := .Values.global.imageTag -}}
{{- if and .Values.global.images .Values.global.images.ui -}}
  {{- $globalTag = .Values.global.images.ui.tag -}}
{{- end -}}
{{- coalesce .Values.ui.image.tag .Values.imageTag $globalTag .Chart.AppVersion -}}
{{- end -}}

# ============================
# ========= GIT-OPS =========
# ============================
{{/*
  get gitops image name from parent, fallback child
*/}}
{{- define "operator.gitopsImageName" -}}
{{- $globalName := "" -}}
{{- if and .Values.global.images .Values.global.images.gitops -}}
  {{- $globalName = .Values.global.images.gitops.name -}}
{{- end -}}
{{- coalesce .Values.gitops.image.name $globalName "apicurio-registry-gitops-sync" -}}
{{- end -}}

{{/*
  get gitops image tag from parent, fallback child
*/}}
{{- define "operator.gitopsImageTag" -}}
{{- $globalTag := .Values.global.imageTag -}}
{{- if and .Values.global.images .Values.global.images.gitops.tag -}}
  {{- $globalTag = .Values.global.images.gitops.tag -}}
{{- end -}}
{{- coalesce .Values.gitops.image.tag .Values.imageTag $globalTag .Chart.AppVersion -}}
{{- end -}}

{{/*
  Format: registry/repository/name:tag
*/}}
{{- define "operator.image" -}}
{{- printf "%s/%s/%s:%s" .registry .repository .name .tag -}}
{{- end -}}

{{/*
  Build image operator
*/}}
{{- define "operator.operatorImage" -}}
{{- include "operator.image" (dict
  "registry"   (include "operator.imageRegistry" .)
  "repository" (include "operator.imageRepository" .)
  "name"       (include "operator.operatorImageName" .)
  "tag"        (include "operator.operatorImageTag" .)
) -}}
{{- end -}}

{{/*
  Build image app
*/}}
{{- define "operator.appImage" -}}
{{- include "operator.image" (dict
  "registry"   (include "operator.imageRegistry" .)
  "repository" (include "operator.imageRepository" .)
  "name"       (include "operator.appImageName" .)
  "tag"        (include "operator.appImageTag" .)
) -}}
{{- end -}}

{{/*
  Build image ui
*/}}
{{- define "operator.uiImage" -}}
{{- include "operator.image" (dict
  "registry"   (include "operator.imageRegistry" .)
  "repository" (include "operator.imageRepository" .)
  "name"       (include "operator.uiImageName" .)
  "tag"        (include "operator.uiImageTag" .)
) -}}
{{- end -}}

{{/*
  Build image gitops
*/}}
{{- define "operator.gitopsImage" -}}
{{- include "operator.image" (dict
  "registry"   (include "operator.imageRegistry" .)
  "repository" (include "operator.imageRepository" .)
  "name"       (include "operator.gitopsImageName" .)
  "tag"        (include "operator.gitopsImageTag" .)
) -}}
{{- end -}}

{{/*
 Selector labels
*/}}
{{- define "operator.selectorLabels" -}}
app: apicurio-operator
app.kubernetes.io/name: {{ include "operator.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
 commons labels
*/}}
{{- define "operator.labels" -}}
{{ include "operator.selectorLabels" . }}
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
{{- define "operator.watchNamespaces" -}}
{{- $namespacesList := .Values.operator.watchNamespaces | default (list) -}}
{{- $returnList := append $namespacesList .Release.Namespace | sortAlpha | uniq -}}
{{- join "," $returnList -}}
{{- end -}}