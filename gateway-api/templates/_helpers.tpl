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
    backendRefs: [{name, port, namespace, weight}]
*/}}
{{- define "gw.httpRouteRules" -}}
{{- if .rules }}
{{ toYaml .rules }}
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
    - name: {{ .name }}
      port: {{ .port }}
      {{- with .namespace }}
      namespace: {{ . }}
      {{- end }}
      {{- with .weight }}
      weight: {{ . }}
      {{- end }}
    {{- end }}
{{- end }}
{{- end }}

{{/*
GRPCRoute rules.
- If `.rules` is set, full passthrough (method/service/header matches, etc.).
- Otherwise a single rule with no `matches` (Gateway API treats a rule with
  no matches as "match everything") pointing at `backendRefs`.
*/}}
{{- define "gw.grpcRouteRules" -}}
{{- if .rules }}
{{ toYaml .rules }}
{{- else }}
- backendRefs:
    {{- range .backendRefs }}
    - name: {{ .name }}
      port: {{ .port }}
      {{- with .namespace }}
      namespace: {{ . }}
      {{- end }}
      {{- with .weight }}
      weight: {{ . }}
      {{- end }}
    {{- end }}
{{- end }}
{{- end }}

{{/*
parentRefs for a route entry, falling back to Values.defaultParentRefs when
the entry doesn't set its own.
*/}}
{{- define "gw.parentRefs" -}}
{{- $refs := .route.parentRefs | default .root.Values.defaultParentRefs -}}
{{- range $refs }}
- name: {{ .name }}
  {{- with .namespace }}
  namespace: {{ . }}
  {{- end }}
  {{- with .sectionName }}
  sectionName: {{ . }}
  {{- end }}
{{- end }}
{{- end }}
