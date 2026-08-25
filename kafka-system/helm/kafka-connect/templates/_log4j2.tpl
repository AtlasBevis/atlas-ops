{{- define "connect.logging.log4j2Content" -}}
{{- $tz := default "Asia/Ho_Chi_Minh" .Values.connect.logging.timezone -}}
name = connectConfig
monitorInterval = 0

appender.console.type = Console
appender.console.name = STDOUT
appender.console.layout.type = JsonTemplateLayout
appender.console.layout.eventTemplateUri = classpath:EcsLayout.json
appender.console.layout.eventTemplateAdditionalField[0].type = EventTemplateAdditionalField
appender.console.layout.eventTemplateAdditionalField[0].key = @timestamp
appender.console.layout.eventTemplateAdditionalField[0].format = JSON
appender.console.layout.eventTemplateAdditionalField[0].value = {"$resolver":"timestamp","pattern":{"format":"yyyy-MM-dd'T'HH:mm:ss.SSSXXX","timeZone":"{{ $tz }}"}}

rootLogger.appenderRefs = console
rootLogger.appenderRef.console.ref = STDOUT
{{- $loggers := .Values.connect.logging.loggers | default dict }}
{{- if not (hasKey $loggers "rootLogger.level") }}
rootLogger.level = INFO
{{- end }}
{{- range $pkg, $level := $loggers }}
{{- if eq $pkg "rootLogger.level" }}
rootLogger.level = {{ $level }}
{{- else }}
logger.{{ $pkg | replace "." "_" }}.name = {{ $pkg }}
logger.{{ $pkg | replace "." "_" }}.level = {{ $level }}
{{- end }}
{{- end }}
{{- end -}}

{{- define "connect.logging.log4j2Checksum" -}}
{{- include "connect.logging.log4j2Content" . | sha256sum -}}
{{- end -}}
