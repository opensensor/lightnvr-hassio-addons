# LightNVR — Home Assistant add-on

Run [LightNVR](https://github.com/opensensor/lightnvr) directly from the Home
Assistant add-on store instead of a standalone Docker/Compose stack.

This folder is a self-contained Home Assistant add-on repository containing a
single add-on, [`lightnvr`](./lightnvr). It wraps the official multi-arch
`ghcr.io/opensensor/lightnvr` image with a thin launcher that maps Home
Assistant storage and options onto LightNVR.

## Distribution: dedicated add-ons repository

Home Assistant expects an add-on repository to have `repository.yaml` at the
**git root**. Since LightNVR's main repo is a monorepo, publish the **contents of
this `homeassistant/` folder** as the root of a dedicated repository, e.g.
`opensensor/lightnvr-hassio-addons`:

```
lightnvr-hassio-addons/        (git root)
├── repository.yaml
└── lightnvr/
    ├── config.yaml
    ├── build.yaml
    ├── Dockerfile
    ├── run.sh · ha-cmd.sh · ha-health.sh
    ├── icon.png · logo.png
    ├── translations/en.yaml
    └── README.md · DOCS.md · CHANGELOG.md
```

One way to create it (run from a checkout of this monorepo):

```bash
gh repo create opensensor/lightnvr-hassio-addons --public \
  --description "Home Assistant add-ons for LightNVR"
tmp=$(mktemp -d) && git -C "$tmp" clone \
  https://github.com/opensensor/lightnvr-hassio-addons .
cp -r homeassistant/. "$tmp/lightnvr-hassio-addons/"
git -C "$tmp/lightnvr-hassio-addons" add -A
git -C "$tmp/lightnvr-hassio-addons" commit -m "LightNVR add-on 0.36.3"
git -C "$tmp/lightnvr-hassio-addons" push
```

The add-on pulls the public `ghcr.io/opensensor/lightnvr` image at build time, so
the dedicated repo is fully self-contained.

### Users then install via:

1. **Settings → Add-ons → Add-on Store → ⋮ → Repositories**.
2. Add `https://github.com/opensensor/lightnvr-hassio-addons` and **Add**.
3. Open **LightNVR** in the store, **Install**, **Start**, **Open Web UI**.

### Local add-on (quickest for testing before the repo exists)

1. Install the **Samba share** or **Advanced SSH & Web Terminal** add-on.
2. Copy this directory's `lightnvr/` subfolder into your Home Assistant
   `/addons` directory, so you have `/addons/lightnvr/config.yaml`.
3. **Settings → Add-ons → Add-on Store → ⋮ → Reload**.
4. **LightNVR** appears under **Local add-ons** — install and start it.

## What you get

- go2rtc streaming with WebRTC/HLS low-latency live view
- ONVIF camera discovery on the LAN (host networking)
- Continuous recording + motion/object detection
- Config & database included in Home Assistant backups; recordings kept out of
  backups under `/media/lightnvr/recordings`
- Web UI on a non-standard default port (`7800`, configurable) to avoid host
  conflicts

See [`lightnvr/DOCS.md`](./lightnvr/DOCS.md) for full details.

> Default login is `admin` / `admin` — change it immediately after first start.
