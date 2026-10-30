# LightNVR — Home Assistant add-ons

> **Part of the [LightNVR project](https://github.com/opensensor/lightnvr).**
> This repository only packages LightNVR as a Home Assistant add-on — the NVR
> source code, full documentation and issue tracker live in the
> [main repository](https://github.com/opensensor/lightnvr).

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
| [**Light Object Detect**](./light_object_detect) | Detection API with ONNX, TFLite, and Coral USB Edge TPU. amd64 / aarch64. |

See [`lightnvr/DOCS.md`](./lightnvr/DOCS.md) for configuration, networking and
storage details.

## How it works

The add-on imports the runtime filesystem from the official multi-arch
`ghcr.io/opensensor/lightnvr` image into its own Docker stage. This avoids
inheriting Docker volume declarations that conflict with Home Assistant's
storage layout. Startup prepares that storage as root, then drops to
UID/GID **10001** before initializing or starting LightNVR and go2rtc.
It uses **host networking** (so ONVIF
discovery and WebRTC work), serves the Web UI on a non-standard default port
(**7800**, configurable), keeps your config and database in Home Assistant
backups, and stores recordings under the Home Assistant **media** folder
(`/media/lightnvr/recordings`) so backups stay small.

## Container regression test

With Docker and Python 3 available:

```sh
docker build -t lightnvr-addon:issue688 lightnvr
python3 tests/test_container.py
```

The test uses disposable volumes without publishing ports. It checks fresh
startup, migration of root-owned data, private file modes, non-root recorder
and go2rtc processes, custom-port healthchecks, and persistence after container
recreation. Set `ADDON_TEST_IMAGE` to test another locally built image.

An optional fourth version component (for example `0.45.0.1`) identifies an
add-on packaging revision; `build.yaml` still pins upstream `0.45.0`. The daily
version sync compares the first three components and preserves packaging fixes
until a newer upstream version is available. When updating the upstream pin,
update both `build.yaml` and the Dockerfile's default `BUILD_FROM`.

## Support

Issues with the NVR itself: <https://github.com/opensensor/lightnvr/issues>.

[add-repo]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fopensensor%2Flightnvr-hassio-addons
[add-repo-shield]: https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg

## Building the detection add-on

```sh
docker build -t light-object-detect-addon:issue2 light_object_detect
python3 tests/test_object_detect.py
```

The Dockerfile pins the upstream source revision and Python dependencies. It
uses the upstream CPU/Coral application without the optional Torch stack.
Update `UPSTREAM_REF` deliberately after validating both native architecture
jobs. The initial revision includes the metadata fix in
[light-object-detect PR #16](https://github.com/opensensor/light-object-detect/pull/16).

The smoke tests run real ONNX and TFLite inference without network access,
check model persistence across container recreation, load the Coral runtime,
and verify that a missing Coral fails startup. Actual USB inference still
requires device testing on Home Assistant OS.
