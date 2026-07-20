# LightNVR — Home Assistant add-on

LightNVR is a lightweight Network Video Recorder built for low-resource
hardware. It integrates [go2rtc](https://github.com/AlexxIT/go2rtc) for
restreaming and low-latency WebRTC/HLS live view, discovers ONVIF cameras,
records continuously, and can run motion/object detection.

This add-on wraps the official multi-arch `ghcr.io/opensensor/lightnvr` image so
you can run it directly from the Home Assistant add-on store instead of a
separate Docker/Compose stack.

## Installation

1. In Home Assistant go to **Settings → Add-ons → Add-on Store**.
2. Either:
   - **Custom repository** — click the ⋮ menu, **Repositories**, and add the
     dedicated add-ons repository URL (see the project README), **or**
   - **Local add-on** — copy the `lightnvr` folder into your Home Assistant
     `/addons` directory (via the *Samba share* or *Advanced SSH & Web Terminal*
     add-on). It then appears under **Local add-ons**.
3. Open **LightNVR** and click **Install**. The first build pulls the base
   image and layers a small wrapper on top (a minute or two, depending on your
   connection — no compilation).
4. Click **Start**, then **Open Web UI**.

## First login

Default credentials are:

- **Username:** `admin`
- **Password:** `admin`

**Change the password immediately** from the LightNVR settings page — with host
networking the Web UI is reachable from anywhere on your LAN.

## Configuration

| Option | Default | Description |
| --- | --- | --- |
| `web_port` | `7800` | Host port for the Web UI (non-standard by default to avoid conflicts). Restart to apply. |
| `max_streams` | `32` | Camera stream slots to allocate (1–256). Restart to apply. |
| `go2rtc_config_persist` | `true` | Keep the go2rtc config between restarts. |
| `onvif_network` | _(blank)_ | CIDR to scan for ONVIF cameras, e.g. `192.168.1.0/24`. Blank = auto. |
| `timezone` | _(blank)_ | Override the timezone. Blank inherits the Home Assistant timezone. |

> If you change `web_port`, the **Open Web UI** button (which is fixed to the
> default `7800`) will point at the wrong port — browse to
> `http://<host-ip>:<web_port>/` instead.

## Networking

The add-on runs with **host networking** so that:

- ONVIF WS-Discovery and mDNS (both multicast) can find cameras on your LAN.
- go2rtc WebRTC candidates are directly reachable for low-latency live view.

The following ports are used **on the host**:

| Port | Purpose |
| --- | --- |
| `7800/tcp` | Web UI (change via the `web_port` option) |
| `8554/tcp` | RTSP restream (go2rtc) |
| `8555/tcp+udp` | WebRTC |
| `1984/tcp` | go2rtc API |

The Web UI defaults to the non-standard port **7800** to avoid clashing with
other host services. If it still conflicts, change the `web_port` option.

## Storage & backups

| Data | Location | In HA backups? |
| --- | --- | --- |
| Config + go2rtc config | add-on `/data/config` | ✅ Yes |
| SQLite database | add-on `/data/lib/database` | ✅ Yes |
| Detection models | add-on `/data/lib/models` | ✅ Yes |
| **Recordings** | **`/media/lightnvr/recordings`** | ❌ No (kept small) |

Recordings are deliberately stored under the Home Assistant **media** folder so
they are *not* pulled into every add-on backup (they can be huge), while your
settings and database *are* backed up. Recordings survive add-on updates and
even an uninstall; delete `/media/lightnvr` manually if you want to reclaim the
space.

Manage retention (days / max size) from LightNVR's own **Settings → Storage**
page.

## Updating

Bump the base image tag in `build.yaml` (and `version` in `config.yaml`) and
rebuild, or wait for a new add-on release. Your config, database and recordings
are preserved across updates because they live on Home Assistant-managed
storage.

## Troubleshooting

- **Cameras not auto-discovered:** set `onvif_network` to your camera subnet in
  CIDR notation, then restart.
- **Live view won't play:** confirm ports `8555/tcp+udp` are not blocked on the
  host firewall; check the add-on log for go2rtc errors.
- **Add-on won't start after an update:** check the **Log** tab. The launcher
  prints the resolved storage paths on start.

For NVR-level issues see the main project documentation and issue tracker at
<https://github.com/opensensor/lightnvr>.
