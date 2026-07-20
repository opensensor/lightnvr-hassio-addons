#!/bin/sh
# Runs as the container CMD, i.e. AFTER the base image entrypoint
# (docker-entrypoint.sh) has created the default lightnvr.ini. This is the
# right moment to pin the Web UI port before LightNVR itself starts.
set -e

PORT="${LIGHTNVR_WEB_PORT:-7800}"
INI="/etc/lightnvr/lightnvr.ini"   # symlink -> /data/config/lightnvr.ini

# Record the active port so the healthcheck can find it (it runs in a fresh
# process that does not inherit our exported environment).
echo "$PORT" > /run/lightnvr.web_port 2>/dev/null || true

# Pin the [web] port. awk tracks the current section so only the [web] port is
# touched — go2rtc's api_port and mqtt's broker_port are left alone. Write back
# through the symlink (cat >), never mv, so the /data symlink is preserved.
if [ -f "$INI" ]; then
    TMP="$(mktemp)"
    awk -v p="$PORT" '
        /^\[/{sec=$0}
        sec=="[web]" && /^[[:space:]]*port[[:space:]]*=/{sub(/=.*/, "= " p)}
        {print}
    ' "$INI" > "$TMP"
    cat "$TMP" > "$INI"
    rm -f "$TMP"
    echo "[lightnvr-addon] Web UI port set to ${PORT}"
else
    echo "[lightnvr-addon] WARN: ${INI} not found; LightNVR will use its default port"
fi

exec /bin/start.sh
