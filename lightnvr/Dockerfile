ARG BUILD_FROM=ghcr.io/opensensor/lightnvr:0.45.1
# hadolint ignore=DL3006
FROM ${BUILD_FROM} AS upstream

# Import the runtime filesystem without the upstream USER/VOLUME metadata.
# The add-on owns persistence via /data and /media. Inherited database/models/
# recordings volumes would become mountpoints that run.sh cannot symlink.
FROM scratch
COPY --from=upstream / /
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    DEBIAN_FRONTEND=noninteractive \
    GO2RTC_CONFIG_PERSIST=true \
    LIGHTNVR_AUTO_INIT=true \
    LIGHTNVR_WEB_ROOT=/var/lib/lightnvr/www

# Root is used only for package installation and storage preparation.
# run.sh drops privileges before invoking the upstream entrypoint.
USER 0:0

# jq is used by run.sh to read the add-on options from /data/options.json.
# The base image is Debian-slim, so install it with apt.
RUN apt-get update \
    && apt-get install -y --no-install-recommends jq \
    && rm -rf /var/lib/apt/lists/*

# HA-specific scripts:
#   ha-run.sh   ENTRYPOINT — wires add-on options + persistent storage, then
#               execs the image's own entrypoint (docker-entrypoint.sh).
#   ha-cmd.sh   CMD — runs after the base init, pins the Web UI port, execs
#               /bin/start.sh (LightNVR, which manages go2rtc).
#   ha-health.sh HEALTHCHECK — probes the configured Web UI port.
COPY run.sh /ha-run.sh
COPY ha-cmd.sh /ha-cmd.sh
COPY ha-health.sh /ha-health.sh
RUN chmod +x /ha-run.sh /ha-cmd.sh /ha-health.sh

# Replace the base healthcheck (which hard-codes port 8080) with one that reads
# the configured port.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["/ha-health.sh"]

ENTRYPOINT ["/ha-run.sh"]
CMD ["/ha-cmd.sh"]
