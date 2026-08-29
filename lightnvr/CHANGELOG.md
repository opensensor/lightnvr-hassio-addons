# Changelog

## 0.41.0

- Update to upstream LightNVR 0.41.0.

## 0.40.7

- Update to upstream LightNVR 0.40.7.

## 0.40.2

- Update to upstream LightNVR 0.40.2.

## 0.40.0

- Update to upstream LightNVR 0.40.0.

## 0.39.2

- Update to upstream LightNVR 0.39.2.

## 0.38.2

- Update to upstream LightNVR 0.38.2.

## 0.37.2

- Update to upstream LightNVR 0.37.2.

## 0.37.1

- Update to upstream LightNVR 0.37.1.

## 0.36.7

- Update to upstream LightNVR 0.36.7.

## 0.36.6

- Update to upstream LightNVR 0.36.6.

## 0.36.5

- Update to upstream LightNVR 0.36.5.

## 0.36.4

- Update to upstream LightNVR 0.36.4.

## 0.36.3

- Initial Home Assistant add-on release.
- Wraps `ghcr.io/opensensor/lightnvr:0.36.3` (amd64 / aarch64 / armv7).
- Host networking for ONVIF discovery and WebRTC live view.
- Web UI on a non-standard default port (`7800`) to avoid host conflicts;
  configurable via the `web_port` option.
- Config + database persisted under the add-on `/data` (included in HA backups);
  recordings stored under `/media/lightnvr/recordings` (excluded from backups).
- Options: `web_port`, `max_streams`, `go2rtc_config_persist`, `onvif_network`,
  `timezone`.
