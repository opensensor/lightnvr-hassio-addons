# Configuration

The default ONNX backend works on CPU without additional hardware. The image
includes the models for all three supported backends, so startup and inference
work without downloading models at runtime.

| Option | Default | Purpose |
| --- | --- | --- |
| `default_backend` | `onnx` | `onnx`, `tflite`, or `edgetpu` |
| `port` | `8000` | Detection API port; change if another service uses it |
| `bind_address` | `127.0.0.1` | Host-local access; `0.0.0.0` also allows LAN clients |
| `confidence_threshold` | `0.5` | Minimum detection confidence, from 0 to 1 |
| `edgetpu_device` | `usb` | Coral device selector, such as `usb` or `usb:0` |

The API has no authentication. Its default loopback binding lets the LightNVR
add-on on the same Home Assistant host connect without exposing it on the LAN.
Only select `0.0.0.0` when access from other trusted machines is needed; do not
forward this port from the internet.

## Connect LightNVR

1. Install and start **Light Object Detect** from this repository.
2. In LightNVR, enable API detection and set its URL to
   `http://127.0.0.1:8000/api/v1/detect` (substitute your configured port).
3. Select the `light-object-detect` request format and the backend matching
   this add-on's `default_backend` option.
4. Enable detection on the desired camera streams.

Both add-ons use host networking, so loopback refers to the same host. A
LightNVR installation on another machine needs the Home Assistant host's IP
and `bind_address: 0.0.0.0` instead.

## Google Coral USB

Connect the Coral USB Accelerator to the Home Assistant host, preferably to a
USB 3 port. Set `default_backend: edgetpu`, leave `edgetpu_device: usb` for a
single device, and restart the add-on. Choose `edgetpu` in LightNVR as well.

The add-on requests USB passthrough with hotplug support using Home Assistant's
[`usb` configuration option](https://contributors.home-assistant.io/apps/reference/configuration/#hardware).
It includes the standard-frequency Edge TPU runtime for both supported
architectures. It does not require full hardware access or protection mode to
be disabled. The service runs as root to access USB device nodes. PCIe/M.2
Coral passthrough is not configured by this add-on.

If the selected Coral cannot initialize, startup fails with the error in the
add-on log. It does not silently switch to CPU or report a healthy detector.
After reconnecting a device that failed, restart the add-on.

## Models and backups

The selected backend's bundled model and labels are copied into private
`/data/models/<backend>` on first use. Existing files are preserved on restart
and upgrade, and are included in Home Assistant backups. Models:

- ONNX: YOLO26n distill, COCO labels.
- TFLite: quantized SSD MobileNet v1, COCO labels.
- Edge TPU: Coral-compiled SSD MobileNet v2, COCO labels.

Only the selected backend is initialized. The image omits the optional
Moondream/Torch stack to reduce installation size and memory use on a Pi.

## Troubleshooting

- **Connection refused:** inspect the add-on log for initialization errors,
  check the configured port, and confirm the service is started.
- **Port already in use:** change `port`, restart, and update LightNVR's URL.
- **Coral initialization fails:** check the USB connection and power, stop
  other services using the Coral, and confirm `edgetpu_device` selects it.
- **A healthy API but no detections:** check the selected backend and confidence
  threshold in both applications. Per-request LightNVR settings can override
  the add-on's default confidence threshold.

The container healthcheck probes the configured port after backend startup.
A healthy check means the selected model loaded and HTTP is responding; it
is not a continuous hardware inference benchmark.
