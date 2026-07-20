#!/bin/sh
# Container healthcheck. The Web UI port is configurable, so read it from the
# file ha-cmd.sh wrote (this process does not inherit the launcher's env).
PORT="$(cat /run/lightnvr.web_port 2>/dev/null || echo 7800)"
curl -fsS "http://127.0.0.1:${PORT}/" >/dev/null 2>&1 || exit 1
