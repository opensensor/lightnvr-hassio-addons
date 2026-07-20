ARG BUILD_FROM
# hadolint ignore=DL3006
FROM ${BUILD_FROM}

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
