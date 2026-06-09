FROM moby/buildkit:v0.30.0-rootless

USER root

LABEL maintainer="dev.binhtt@gmail.com"

RUN apk add --no-cache \
    git \
    bash \
    make \
    openssh-client \
    ca-certificates \
    curl

ENV BUILDKITD_FLAGS=--oci-worker-no-process-sandbox

RUN mkdir -p /home/appuser/.ssh \
    && chown -R 1000:1000 /home/appuser

ENV HOME=/home/appuser
    
USER 1000

WORKDIR $HOME

CMD ["sh"]
