FROM debian:bookworm-slim

LABEL maintainer="dev.binhtt@gmail.com"

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    ca-certificates \
    curl \
    make \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*