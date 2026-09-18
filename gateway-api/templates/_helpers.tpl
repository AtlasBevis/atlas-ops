{{/*
Common labels applied to every resource this chart renders.
*/}}
{{- define "gw.labels" -}}
app.kubernetes.io/part-of: gateway-api
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
HTTPRoute rules.
- If `.rules` is set on the route entry, it is used as-is (full passthrough,
  for anything the shorthand below can't express: header/query matches,
  multiple weighted backends, filters, redirects, mirrors, ...).
- Otherwise a single rule is built from the shorthand fields:
    path      (default "/")
    pathType  (default "PathPrefix")
    filters   (optional, passthrough)
    backendRefs: [{name, port, namespace, weight, group, kind}]

Note: `group`, `kind` (on backendRefs) and `weight` are set explicitly here
(matching the Gateway API server-side defaults: group "", kind "Service",
weight 1) so the rendered manifest matches the live object byte-for-byte —
otherwise Argo CD shows a permanent false diff after the API server fills
those fields in on the stored object.
*/}}
{{- define "gw.httpRouteRules" -}}
{{- if .rules }}
{{- range .rules }}
- {{- with .name }}
  name: {{ . }}
  {{- end }}
  {{- with .matches }}
  matches:
    {{- toYaml . | nindent 4 }}
  {{- end }}
  {{- with .filters }}
  filters:
    {{- toYaml . | nindent 4 }}
  {{- end }}
  {{- with .backendRefs }}
  backendRefs:
    {{- range . }}
    - group: {{ .group | default "" | quote }}
      kind: {{ .kind | default "Service" }}
      name: {{ .name }}
      port: {{ .port }}
      weight: {{ .weight | default 1 }}
      {{- with .namespace }}
      namespace: {{ . }}
      {{- end }}
    {{- end }}
  {{- end }}
  {{- with .timeouts }}
  timeouts:
    {{- toYaml . | nindent 4 }}
  {{- end }}
  {{- with .sessionPersistence }}
  sessionPersistence:
    {{- toYaml . | nindent 4 }}
  {{- end }}
{{- end }}
{{- else }}
- matches:
    - path:
        type: {{ .pathType | default "PathPrefix" }}
        value: {{ .path | default "/" | quote }}
  {{- with .filters }}
  filters:
    {{- toYaml . | nindent 4 }}
  {{- end }}
  backendRefs:
    {{- range .backendRefs }}
    - group: {{ .group | default "" | quote }}
      kind: {{ .kind | default "Service" }}
      name: {{ .name }}
      port: {{ .port }}
      weight: {{ .weight | default 1 }}
      {{- with .namespace }}
      namespace: {{ . }}
      {{- end }}
    {{- end }}
{{- end }}
{{- end }}

{{/*
GRPCRoute rules.
- If `.rules` is set, full passthrough (method/service/header matches, etc.).
- Otherwise a single rule with no `matches` (Gateway API treats a rule with
  no matches as "match everything") pointing at `backendRefs`.
Same explicit group/kind/weight defaulting as gw.httpRouteRules, for the
same reason (avoid a permanent Argo CD diff against server-defaulted fields).
*/}}
{{- define "gw.grpcRouteRules" -}}
{{- if .rules }}
{{- range .rules }}
- {{- with .name }}
  name: {{ . }}
  {{- end }}
  {{- with .matches }}
  matches:
    {{- toYaml . | nindent 4 }}
  {{- end }}
  {{- with .filters }}
  filters:
    {{- toYaml . | nindent 4 }}
  {{- end }}
  {{- with .backendRefs }}
  backendRefs:
    {{- range . }}
    - group: {{ .group | default "" | quote }}
      kind: {{ .kind | default "Service" }}
      name: {{ .name }}
      port: {{ .port }}
      weight: {{ .weight | default 1 }}
      {{- with .namespace }}
      namespace: {{ . }}
      {{- end }}
    {{- end }}
  {{- end }}
  {{- with .sessionPersistence }}
  sessionPersistence:
    {{- toYaml . | nindent 4 }}
  {{- end }}
{{- end }}
{{- else }}
- backendRefs:
    {{- range .backendRefs }}
    - group: {{ .group | default "" | quote }}
      kind: {{ .kind | default "Service" }}
      name: {{ .name }}
      port: {{ .port }}
      weight: {{ .weight | default 1 }}
      {{- with .namespace }}
      namespace: {{ . }}
      {{- end }}
    {{- end }}
{{- end }}
{{- end }}

{{/*
parentRefs for a route entry, falling back to Values.defaultParentRefs when
the entry doesn't set its own. `group`/`kind` are set explicitly (defaults:
"gateway.networking.k8s.io" / "Gateway") for the same reason as above.
*/}}
{{- define "gw.parentRefs" -}}
{{- $refs := .route.parentRefs | default .root.Values.defaultParentRefs -}}
{{- range $refs }}
- group: {{ .group | default "gateway.networking.k8s.io" | quote }}
  kind: {{ .kind | default "Gateway" }}
  name: {{ .name }}
  {{- with .namespace }}
  namespace: {{ . }}
  {{- end }}
  {{- with .sectionName }}
  sectionName: {{ . }}
  {{- end }}
{{- end }}
{{- end }}
