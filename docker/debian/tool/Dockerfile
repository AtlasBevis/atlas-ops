FROM debian:bookworm-slim

LABEL maintainer="dev.binhtt@gmail.com"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget ca-certificates \
    dnsutils \
    jq \
    dnsutils iputils-ping iproute2 netcat-openbsd \
    openssl vim-tiny less procps git \
    python3 \
    && rm -rf /var/lib/apt/lists/*

RUN echo 'alias ll="ls -la"' >> /root/.bashrc

WORKDIR /root

CMD ["sleep", "infinity"]