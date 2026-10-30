# Light Object Detect

Object detection for LightNVR on Home Assistant OS or Supervised. Supports
ONNX and TensorFlow Lite on CPU, plus Google Coral USB Edge TPU acceleration
on amd64 and aarch64.

Install **Light Object Detect** from this repository, start it, then set
LightNVR's **API Detection URL** to:

```text
http://127.0.0.1:8000/api/v1/detect
```

Use the `light-object-detect` request format and choose the same backend in
LightNVR as the add-on's `default_backend`. See [DOCS.md](DOCS.md) for options,
Coral setup, and troubleshooting.
