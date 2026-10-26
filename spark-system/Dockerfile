ARG SPARK_IMAGE=apache/spark:4.1.3-scala2.13-java21-python3-ubuntu

FROM alpine:3.24 AS loader

ARG ICEBERG_VERSION=1.12.0
ARG SPARK_VERSION=4.1
ARG SCALA_VERSION=2.13
ARG MVN=https://repo.maven.apache.org/maven2

RUN apk add --no-cache curl \
    && mkdir -p /tmp/iceberg \
    && set -eux; \
    URLS="\
${MVN}/org/apache/iceberg/iceberg-spark-runtime-${SPARK_VERSION}_${SCALA_VERSION}/${ICEBERG_VERSION}/iceberg-spark-runtime-${SPARK_VERSION}_${SCALA_VERSION}-${ICEBERG_VERSION}.jar \
${MVN}/org/apache/iceberg/iceberg-aws-bundle/${ICEBERG_VERSION}/iceberg-aws-bundle-${ICEBERG_VERSION}.jar \
${MVN}/org/apache/hadoop/hadoop-aws/3.4.2/hadoop-aws-3.4.2.jar \
${MVN}/software/amazon/awssdk/bundle/2.29.52/bundle-2.29.52.jar \
${MVN}/io/openlineage/openlineage-spark_2.13/1.52.0/openlineage-spark_2.13-1.52.0.jar \
${MVN}/org/apache/kafka/kafka-clients/4.0.0/kafka-clients-4.0.0.jar \
${MVN}/com/microsoft/sqlserver/mssql-jdbc/12.8.1.jre11/mssql-jdbc-12.8.1.jre11.jar \
${MVN}/com/mysql/mysql-connector-j/8.4.0/mysql-connector-j-8.4.0.jar \
${MVN}/com/oracle/database/jdbc/ojdbc11/23.5.0.24.07/ojdbc11-23.5.0.24.07.jar \
${MVN}/com/clickhouse/clickhouse-jdbc/0.3.2/clickhouse-jdbc-0.3.2-all.jar \
${MVN}/org/postgresql/postgresql/42.7.14/postgresql-42.7.14.jar \
"; \
    for url in $URLS; do \
        curl -fSL --retry 3 \
            "$url" \
            -o "/tmp/iceberg/$(basename "$url")"; \
    done; \
    chmod 644 /tmp/iceberg/*.jar

FROM ${SPARK_IMAGE} AS spark

USER root

COPY --from=loader /tmp/iceberg/*.jar /opt/spark/jars/

RUN chmod 644 /opt/spark/jars/*.jar

WORKDIR /opt/spark/jobs

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --no-compile -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

COPY --chown=spark:spark jobs/ /opt/spark/jobs/

WORKDIR /opt/spark/work-dir

USER spark
