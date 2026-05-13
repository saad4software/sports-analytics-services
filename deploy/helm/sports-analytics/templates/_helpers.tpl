{{/*
Common naming + label helpers for the sports-analytics chart.
*/}}

{{- define "sports-analytics.fullname" -}}
{{- printf "%s" (.Release.Name) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "sports-analytics.labels" -}}
app.kubernetes.io/name: sports-analytics
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{- end -}}

{{- define "sports-analytics.componentLabels" -}}
{{ include "sports-analytics.labels" . }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{- define "sports-analytics.componentSelector" -}}
app.kubernetes.io/name: sports-analytics
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{/*
Resolve the image reference for a service. Uses the global registry when set
and falls back to the per-service repository.
*/}}
{{- define "sports-analytics.image" -}}
{{- $registry := .Values.global.imageRegistry | default "" -}}
{{- $repo := .repository -}}
{{- $tag := .tag | default .Values.image.tag -}}
{{- if $registry -}}
{{- printf "%s/%s:%s" $registry $repo $tag -}}
{{- else -}}
{{- printf "%s:%s" $repo $tag -}}
{{- end -}}
{{- end -}}

{{- define "sports-analytics.secretName" -}}
{{- if .Values.secrets.existingSecret -}}
{{- .Values.secrets.existingSecret -}}
{{- else -}}
{{ include "sports-analytics.fullname" . }}-secrets
{{- end -}}
{{- end -}}

{{- define "sports-analytics.configMapName" -}}
{{ include "sports-analytics.fullname" . }}-config
{{- end -}}

{{/*
Render imagePullSecrets if any.
*/}}
{{- define "sports-analytics.imagePullSecrets" -}}
{{- with .Values.global.imagePullSecrets -}}
imagePullSecrets:
{{- range . }}
  - name: {{ . }}
{{- end }}
{{- end -}}
{{- end -}}
