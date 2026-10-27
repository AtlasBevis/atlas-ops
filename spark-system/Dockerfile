ARG SPARK_IMAGE=apache/spark:4.1.3-scala2.13-java21-python3-ubuntu

FROM alpine:3.24 AS loader

ARG SPARK_VERSION=4.1.3
ARG SPARK_MINOR=4.1
ARG SCALA_VERSION=2.13
ARG ICEBERG_VERSION=1.12.0
ARG HADOOP_VERSION=3.4.2
ARG AWS_SDK_VERSION=2.29.52
ARG OPENLINEAGE_SPARK=1.52.0
ARG KAFKA_CLIENT_VERSION=3.9.2
ARG CLICKHOUSE_VERSION=0.11.0
ARG POSTGRES_VERSION=42.7.14
ARG MYSQL_VERSION=8.4.0
ARG MVN=https://repo.maven.apache.org/maven2

RUN apk add --no-cache curl \
    && mkdir -p /tmp/jars \
    && set -eux; \
    URLS="\
    ${MVN}/org/apache/iceberg/iceberg-spark-runtime-${SPARK_MINOR}_${SCALA_VERSION}/${ICEBERG_VERSION}/iceberg-spark-runtime-${SPARK_MINOR}_${SCALA_VERSION}-${ICEBERG_VERSION}.jar \
    ${MVN}/org/apache/iceberg/iceberg-aws-bundle/${ICEBERG_VERSION}/iceberg-aws-bundle-${ICEBERG_VERSION}.jar \
    ${MVN}/org/apache/hadoop/hadoop-aws/${HADOOP_VERSION}/hadoop-aws-${HADOOP_VERSION}.jar \
    ${MVN}/software/amazon/awssdk/bundle/${AWS_SDK_VERSION}/bundle-${AWS_SDK_VERSION}.jar \
    ${MVN}/io/openlineage/openlineage-spark_${SCALA_VERSION}/${OPENLINEAGE_SPARK}/openlineage-spark_${SCALA_VERSION}-${OPENLINEAGE_SPARK}.jar \
    ${MVN}/org/apache/spark/spark-sql-kafka-0-10_${SCALA_VERSION}/${SPARK_VERSION}/spark-sql-kafka-0-10_${SCALA_VERSION}-${SPARK_VERSION}.jar \
    ${MVN}/org/apache/spark/spark-token-provider-kafka-0-10_${SCALA_VERSION}/${SPARK_VERSION}/spark-token-provider-kafka-0-10_${SCALA_VERSION}-${SPARK_VERSION}.jar \
    ${MVN}/org/apache/kafka/kafka-clients/${KAFKA_CLIENT_VERSION}/kafka-clients-${KAFKA_CLIENT_VERSION}.jar \
    ${MVN}/org/apache/commons/commons-pool2/2.12.1/commons-pool2-2.12.1.jar \
    ${MVN}/com/microsoft/sqlserver/mssql-jdbc/12.8.1.jre11/mssql-jdbc-12.8.1.jre11.jar \
    ${MVN}/com/mysql/mysql-connector-j/${MYSQL_VERSION}}/mysql-connector-j-${MYSQL_VERSION}}.jar \
    ${MVN}/com/oracle/database/jdbc/ojdbc11/23.5.0.24.07/ojdbc11-23.5.0.24.07.jar \
    ${MVN}/com/clickhouse/clickhouse-jdbc/${CLICKHOUSE_VERSION}/clickhouse-jdbc-${CLICKHOUSE_VERSION}-all.jar \
    ${MVN}/org/postgresql/postgresql/${POSTGRES_VERSION}/postgresql-${POSTGRES_VERSION}.jar \
    "; \
    for url in $URLS; do \
    curl -fSL --retry 3 "$url" -o "/tmp/jars/$(basename "$url")"; \
    done; \
    chmod 644 /tmp/jars/*.jar

FROM ${SPARK_IMAGE} AS spark

USER root

COPY --from=loader /tmp/jars/ /opt/spark/jars/

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --no-compile -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

# should define jobs per repostory then use copy this 
COPY --chown=spark:spark jobs/ /opt/spark/jobs/

WORKDIR /opt/spark/work-dir

USER spark
