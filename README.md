# LightNVR — Home Assistant add-ons

Run [LightNVR](https://github.com/opensensor/lightnvr) — a lightweight Network
Video Recorder with go2rtc streaming, WebRTC/HLS live view, ONVIF discovery and
motion/object detection — directly from the Home Assistant add-on store.

## Install

[![Add repository to your Home Assistant instance.][add-repo-shield]][add-repo]

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store**.
2. Click the ⋮ menu (top-right) → **Repositories**.
3. Add:
   ```
   https://github.com/opensensor/lightnvr-hassio-addons
   ```
4. Find **LightNVR** in the store, click **Install**, then **Start**.
5. Click **Open Web UI** and log in with `admin` / `admin` —
   **change the password immediately** (host networking exposes the UI on your
   LAN).

## Add-ons in this repository

| Add-on | Description |
| --- | --- |
| [**LightNVR**](./lightnvr) | Lightweight NVR wrapping `ghcr.io/opensensor/lightnvr` — go2rtc, WebRTC/HLS, ONVIF, recording. amd64 / aarch64. |

See [`lightnvr/DOCS.md`](./lightnvr/DOCS.md) for configuration, networking and
storage details.

## How it works

The add-on layers a thin launcher on top of the official multi-arch
`ghcr.io/opensensor/lightnvr` image. It uses **host networking** (so ONVIF
discovery and WebRTC work), serves the Web UI on a non-standard default port
(**7800**, configurable), keeps your config and database in Home Assistant
backups, and stores recordings under the Home Assistant **media** folder
(`/media/lightnvr/recordings`) so backups stay small.

## Support

Issues with the NVR itself: <https://github.com/opensensor/lightnvr/issues>.

[add-repo]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fopensensor%2Flightnvr-hassio-addons
[add-repo-shield]: https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg
