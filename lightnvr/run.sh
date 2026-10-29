#!/bin/sh
# Home Assistant add-on launcher for LightNVR.
#
# Responsibilities:
#   1. Translate add-on options (/data/options.json) into the environment
#      variables that LightNVR's own entrypoint understands.
#   2. Redirect LightNVR's config, database and recordings onto Home
#      Assistant-managed persistent storage so nothing is lost when the add-on
#      is updated (which recreates the container).
#   3. Hand off to the base image's entrypoint unchanged.
#
# Storage layout:
#   /data/config            -> LightNVR config + go2rtc config (in HA backups)
#   /data/lib/database       -> SQLite database                (in HA backups)
#   /data/lib/models         -> detection models               (in HA backups)
#   /media/lightnvr/recordings -> recordings (large; NOT in HA backups)
#
# The Dockerfile imports the upstream filesystem without its volume metadata,
# allowing these paths to be symlinks into Supervisor-managed storage.
set -e

if [ "$(id -u)" != 0 ]; then
    echo "[lightnvr-addon] Storage preparation must start as root; the recorder runs as UID 10001." >&2
    exit 1
fi

OPTIONS="/data/options.json"

opt() {
    # opt <jq-filter> <default>
    # NOTE: do NOT use jq's `//` operator here — it treats a literal `false`
    # as empty, which would wrongly fall back to the default for boolean
    # options. Read the value directly and null-check instead.
    value="null"
    if [ -f "$OPTIONS" ]; then
        value="$(jq -r "$1" "$OPTIONS" 2>/dev/null || echo null)"
    fi
    if [ -z "${value}" ] || [ "${value}" = "null" ]; then
        echo "$2"
    else
        echo "$value"
    fi
}

WEB_PORT="$(opt '.web_port' '7800')"
MAX_STREAMS="$(opt '.max_streams' '32')"
GO2RTC_PERSIST="$(opt '.go2rtc_config_persist' 'true')"
ONVIF_NETWORK="$(opt '.onvif_network' '')"
TIMEZONE="$(opt '.timezone' '')"

export LIGHTNVR_AUTO_INIT="true"
# Consumed by /ha-cmd.sh (after the base entrypoint has written the default
# config) to pin the Web UI port in lightnvr.ini before LightNVR starts.
export LIGHTNVR_WEB_PORT="${WEB_PORT}"
export MAX_STREAMS
export GO2RTC_CONFIG_PERSIST="${GO2RTC_PERSIST}"
[ -n "${ONVIF_NETWORK}" ] && export LIGHTNVR_ONVIF_NETWORK="${ONVIF_NETWORK}"
# The Supervisor already injects TZ from the Home Assistant timezone; only
# override it when the user set one explicitly in the add-on options.
[ -n "${TIMEZONE}" ] && export TZ="${TIMEZONE}"

# --- Persistent storage targets -------------------------------------------
mkdir -p \
    /data/config/go2rtc \
    /data/lib/database \
    /data/lib/models \
    /media/lightnvr/recordings/mp4

# Persist configuration through symlinks into the add-on data directory.
if [ ! -L /etc/lightnvr/lightnvr.ini ]; then
    rm -f /etc/lightnvr/lightnvr.ini
    ln -s /data/config/lightnvr.ini /etc/lightnvr/lightnvr.ini
fi
if [ ! -L /etc/lightnvr/go2rtc ]; then
    rm -rf /etc/lightnvr/go2rtc
    ln -s /data/config/go2rtc /etc/lightnvr/go2rtc
fi

# Redirect data paths. Recordings go to /media so backups stay small.
link_out() {
    # link_out <path-inside-data-volume> <target>
    if [ ! -L "$1" ]; then
        rm -rf "$1"
        ln -s "$2" "$1"
    fi
}
link_out /var/lib/lightnvr/data/database   /data/lib/database
link_out /var/lib/lightnvr/data/models     /data/lib/models
link_out /var/lib/lightnvr/data/recordings /media/lightnvr/recordings

echo "[lightnvr-addon] Storage wired:"
echo "[lightnvr-addon]   config + database -> /data (included in HA backups)"
echo "[lightnvr-addon]   recordings        -> /media/lightnvr/recordings"
echo "[lightnvr-addon] Options: web_port=${WEB_PORT} max_streams=${MAX_STREAMS} go2rtc_persist=${GO2RTC_PERSIST} onvif_network=${ONVIF_NETWORK:-<none>}"

# Migrate only this add-on's storage, including root-owned pre-0.44 installs.
# Walk real targets explicitly: find does not follow the symlinks above.
# Preserve modes (notably 0600 credentials) and leave recording files alone;
# writable directories allow retention to remove old root-owned segments.
mkdir -p /var/log/lightnvr /var/run/lightnvr
find /data /data/lib /media/lightnvr /var/lib/lightnvr/data -maxdepth 0 \
    \( ! -user 10001 -o ! -group 10001 \) -exec chown -h 10001:10001 {} +
find /data/config /data/lib/database /data/lib/models \
    /var/log/lightnvr /var/run/lightnvr \
    \( ! -user 10001 -o ! -group 10001 \) -exec chown -h 10001:10001 {} +
find /media/lightnvr/recordings -type d \
    \( ! -user 10001 -o ! -group 10001 \) -exec chown -h 10001:10001 {} +

# Older configs used a PID file directly in root-owned /run. Migrate that
# default before upstream initialization; preserve explicitly customized paths.
if [ -f /data/config/lightnvr.ini ]; then
    sed -i -E 's@^(pid_file[[:space:]]*=[[:space:]]*)/var/run/lightnvr\.pid([[:space:]]*([;#].*)?)$@\1/var/run/lightnvr/lightnvr.pid\2@' /data/config/lightnvr.ini
fi

# Configuration initialization, go2rtc generation, and the recorder all run
# unprivileged. Do not invoke the base image's root migration: it cannot follow
# our storage symlinks to fix their targets.
exec setpriv --reuid=10001 --regid=10001 --clear-groups -- \
    /usr/local/bin/docker-entrypoint.sh "$@"
