"""Translate Supervisor options before importing the detector application."""
import json
import os
from pathlib import Path
import shutil


MODELS = {
    "onnx": ("yolo26n-distill.onnx", "coco.txt"),
    "tflite": ("ssd_mobilenet_v1.tflite", "labelmap.txt"),
    "edgetpu": ("ssd_mobilenet_v2_coco_quant_postprocess_edgetpu.tflite", "coco_labels.txt"),
}


def configure(options, app_dir=Path("/app"), data_dir=Path("/data")):
    backend = options.get("default_backend", "onnx")
    port = options.get("port", 8000)
    bind_address = options.get("bind_address", "127.0.0.1")
    threshold = options.get("confidence_threshold", 0.5)
    if backend not in MODELS:
        raise ValueError("default_backend must be onnx, tflite, or edgetpu")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    if bind_address not in ("127.0.0.1", "0.0.0.0"):
        raise ValueError("bind_address must be 127.0.0.1 or 0.0.0.0")
    if type(threshold) not in (int, float) or not 0 <= threshold <= 1:
        raise ValueError("confidence_threshold must be between 0 and 1")

    target = data_dir / "models" / backend
    target.mkdir(parents=True, exist_ok=True)
    for name in MODELS[backend]:
        if not (target / name).exists():
            shutil.copyfile(app_dir / "backends" / backend / "models" / name, target / name)
    model, labels = MODELS[backend]
    env = {
        "DEFAULT_BACKEND": backend,
        # Only load the selected engine; do not try unrelated models at boot.
        "AVAILABLE_BACKENDS": json.dumps([backend]),
        f"{backend.upper()}_MODEL_PATH": str(target / model),
        f"{backend.upper()}_LABELS_PATH": str(target / labels),
        f"{backend.upper()}_CONFIDENCE_THRESHOLD": str(threshold),
        "EDGETPU_DEVICE": options.get("edgetpu_device", "usb"),
        "ONNX_EXECUTION_PROVIDERS": "cpu",
    }
    return env, ["uvicorn", "ha_app:app", "--host", bind_address, "--port", str(port)]


def main():
    options_path = Path("/data/options.json")
    options = json.loads(options_path.read_text()) if options_path.exists() else {}
    env, command = configure(options)
    os.environ.update(env)
    Path("/run/light-object-detect.port").write_text(command[-1])
    print(f"[light-object-detect] Backend: {env['DEFAULT_BACKEND']}; port: {command[-1]}", flush=True)
    os.execvp(command[0], command)


if __name__ == "__main__":
    main()
