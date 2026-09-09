FROM redis:8.10.1-alpine3.23

COPY --chown=redis:redis redis.conf /usr/local/etc/redis/redis.conf
COPY --chmod=0755 docker-entrypoint.sh /usr/local/bin/docker-entrypoint-custom.sh

USER redis

WORKDIR /data

VOLUME ["/data"]

EXPOSE 6379

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD redis-cli ping | grep -q PONG || exit 1

CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]

ENTRYPOINT ["/usr/local/bin/docker-entrypoint-custom.sh"]
