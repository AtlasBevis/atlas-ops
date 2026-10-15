{{/*
Expand the name of the chart.
*/}}
{{- define "operator.name" -}}
{{- .Values.nameOverride | default .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
  get operator image registry from local, fallback global
*/}}
{{- define "operator.imageRegistry" -}}
{{- $global := get .Values "global" | default dict -}}
{{- coalesce .Values.imageRegistry (get $global "imageRegistry") "quay.io" -}}
{{- end -}}

{{/*
  get operator image repository from local, fallback global
*/}}
{{- define "operator.imageRepository" -}}
{{- $global := get .Values "global" | default dict -}}
{{- coalesce .Values.imageRepository (get $global "imageRepository") "apicurio" -}}
{{- end -}}

{{/*
  get operator image pull policy from local, fallback global
*/}}
{{- define "operator.imagePullPolicy" -}}
{{- $global := get .Values "global" | default dict -}}
{{- coalesce .Values.imagePullPolicy (get $global "imagePullPolicy") "IfNotPresent" -}}
{{- end -}}

{{/*
  get operator image pull secrets from local, fallback global
*/}}
{{- define "operator.imagePullSecrets" -}}
{{- $global := get .Values "global" | default dict -}}
{{- $secrets := coalesce .Values.imagePullSecrets (get $global "imagePullSecrets") -}}
{{- if $secrets -}}
{{ toYaml $secrets }}
{{- end -}}
{{- end -}}

# ============================
# ========= OPERATOR =========
# ============================
{{/*
  get operator image name from local, fallback global
*/}}
{{- define "operator.operatorImageName" -}}
{{- $global := get .Values "global" | default dict -}}
{{- $images := get $global "images" | default dict -}}
{{- $globalImage := get $images "operator" | default dict -}}
{{- $globalName := coalesce (get $globalImage "name") (get $globalImage "repository") -}}
{{- coalesce .Values.operator.image.name $globalName "apicurio-registry-3-operator" -}}
{{- end -}}

{{/*
  get operator image tag from local, fallback global
*/}}
{{- define "operator.operatorImageTag" -}}
{{- $global := get .Values "global" | default dict -}}
{{- $images := get $global "images" | default dict -}}
{{- $globalImage := get $images "operator" | default dict -}}
{{- $globalTag := coalesce (get $globalImage "tag") (get $global "imageTag") -}}
{{- coalesce .Values.operator.image.tag .Values.imageTag $globalTag .Chart.AppVersion -}}
{{- end -}}

# ============================
# ========= APP =============
# ============================
{{/*
  get app image name from local, fallback global
*/}}
{{- define "operator.appImageName" -}}
{{- $global := get .Values "global" | default dict -}}
{{- $images := get $global "images" | default dict -}}
{{- $globalImage := get $images "app" | default dict -}}
{{- $globalName := coalesce (get $globalImage "name") (get $globalImage "repository") -}}
{{- coalesce .Values.app.image.name $globalName "apicurio-registry" -}}
{{- end -}}

{{/*
  get app image tag from local, fallback global
*/}}
{{- define "operator.appImageTag" -}}
{{- $global := get .Values "global" | default dict -}}
{{- $images := get $global "images" | default dict -}}
{{- $globalImage := get $images "app" | default dict -}}
{{- $globalTag := coalesce (get $globalImage "tag") (get $global "imageTag") -}}
{{- coalesce .Values.app.image.tag .Values.imageTag $globalTag .Chart.AppVersion -}}
{{- end -}}

# ============================
# ========= UI =========
# ============================
{{/*
  get ui image name from local, fallback global
*/}}
{{- define "operator.uiImageName" -}}
{{- $global := get .Values "global" | default dict -}}
{{- $images := get $global "images" | default dict -}}
{{- $globalImage := get $images "ui" | default dict -}}
{{- $globalName := coalesce (get $globalImage "name") (get $globalImage "repository") -}}
{{- coalesce .Values.ui.image.name $globalName "apicurio-registry-ui" -}}
{{- end -}}

{{/*
  get ui image tag from local, fallback global
*/}}
{{- define "operator.uiImageTag" -}}
{{- $global := get .Values "global" | default dict -}}
{{- $images := get $global "images" | default dict -}}
{{- $globalImage := get $images "ui" | default dict -}}
{{- $globalTag := coalesce (get $globalImage "tag") (get $global "imageTag") -}}
{{- coalesce .Values.ui.image.tag .Values.imageTag $globalTag .Chart.AppVersion -}}
{{- end -}}

# ============================
# ========= GIT-OPS =========
# ============================
{{/*
  get gitops image name from local, fallback global
*/}}
{{- define "operator.gitopsImageName" -}}
{{- $global := get .Values "global" | default dict -}}
{{- $images := get $global "images" | default dict -}}
{{- $globalImage := get $images "gitops" | default dict -}}
{{- $globalName := coalesce (get $globalImage "name") (get $globalImage "repository") -}}
{{- coalesce .Values.gitops.image.name $globalName "apicurio-registry-gitops-sync" -}}
{{- end -}}

{{/*
  get gitops image tag from local, fallback global
*/}}
{{- define "operator.gitopsImageTag" -}}
{{- $global := get .Values "global" | default dict -}}
{{- $images := get $global "images" | default dict -}}
{{- $globalImage := get $images "gitops" | default dict -}}
{{- $globalTag := coalesce (get $globalImage "tag") (get $global "imageTag") -}}
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

{{/*
Create service account name with optional override.
*/}}
{{- define "operator.serviceAccountName" -}}
{{- .Values.serviceAccount.name | default (printf "%s-sa" (include "operator.name" .)) -}}
{{- end -}}