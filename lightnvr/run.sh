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
# The base image declares VOLUME ["/etc/lightnvr", "/var/lib/lightnvr/data"],
# so the Supervisor mounts fresh anonymous volumes over those paths on every
# container (re)creation. We therefore never replace those mountpoints; instead
# we place symlinks *inside* them that point out to /data and /media.
set -e

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

# Config directory (/etc/lightnvr is an anonymous volume): persist the two
# things that matter via symlinks that point out to /data.
if [ ! -L /etc/lightnvr/lightnvr.ini ]; then
    rm -f /etc/lightnvr/lightnvr.ini
    ln -s /data/config/lightnvr.ini /etc/lightnvr/lightnvr.ini
fi
if [ ! -L /etc/lightnvr/go2rtc ]; then
    rm -rf /etc/lightnvr/go2rtc
    ln -s /data/config/go2rtc /etc/lightnvr/go2rtc
fi

# Data directory (/var/lib/lightnvr/data is an anonymous volume): redirect the
# persistent sub-paths. Recordings go to /media so backups stay small.
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

# Hand off to the base image entrypoint (init + go2rtc config regen + signal
# handling). The CMD passed here (/ha-cmd.sh) runs *after* the entrypoint has
# generated the default config, so it can pin the Web UI port before start.
exec /usr/local/bin/docker-entrypoint.sh "$@"
