FROM python:3.12.13-slim

ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/home/appuser

LABEL maintainer="dev.binhtt@gmail.com"

RUN apt-get update && apt-get install -y --no-install-recommends \
    rsync \
    git \
    bash \
    openssh-client \
    ca-certificates \
    curl \
    make \
    jq \
    yq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    ruff==0.15.13 \
    pytest==9.0.3

RUN groupadd -g 1000 appuser && useradd -u 1000 -g appuser -m appuser

COPY --chown=1000:1000 ci/ /opt/ci/
RUN find /opt/ci -type f -exec chmod +x {} +

USER appuser

WORKDIR $HOME

CMD ["bash"]

ENTRYPOINT ["/opt/ci/entrypoint.sh"]