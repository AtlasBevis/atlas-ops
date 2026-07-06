ARG STRIMZI_VERSION=1.0.1
ARG KAFKA_VERSION=4.2.0

FROM quay.io/strimzi/kafka:${STRIMZI_VERSION}-kafka-${KAFKA_VERSION}

LABEL maintainer="dev.binhtt@gmail.com"

USER root:root

RUN mkdir -p /opt/kafka/plugins/{debezium-postgres,debezium-mysql,debezium-sqlserver,debezium-oracle,minio,iceberg,apicurio}

COPY plugins/debezium-postgres/         /opt/kafka/plugins/debezium-postgres/
COPY plugins/debezium-mysql/            /opt/kafka/plugins/debezium-mysql/
COPY plugins/debezium-sqlserver/        /opt/kafka/plugins/debezium-sqlserver/
COPY plugins/debezium-oracle/           /opt/kafka/plugins/debezium-oracle/
COPY plugins/s3-kafkaconnect/           /opt/kafka/plugins/minio/
COPY plugins/iceberg-kafkaconnect/      /opt/kafka/plugins/iceberg/
COPY plugins/apicurio/                  /opt/kafka/plugins/apicurio/

USER 1001