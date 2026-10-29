FROM spark:4.1.3

USER root

COPY jobs/ /opt/spark/jobs/

COPY src/lakehouse /opt/spark/jobs/lakehouse

COPY configs /opt/app/config

RUN chmod 644 /opt/spark/jobs/*.py \
    && chmod -R a+rX /opt/spark/jobs/lakehouse /opt/app/config

ENV LAKEHOUSE_CONFIG_DIR=/opt/app/config

WORKDIR /opt/spark/work-dir

USER 185
