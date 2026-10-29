"""Smoke-test the CPU backends offline; Coral inference needs physical hardware."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import subprocess
import time
import unittest
import uuid

from test_container import docker

IMAGE = os.environ.get("DETECT_TEST_IMAGE", "light-object-detect-addon:issue2")
spec = importlib.util.spec_from_file_location(
    "detect_run", Path(__file__).resolve().parents[1] / "light_object_detect" / "run.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def logs(name):
    # uvicorn writes startup failures to stderr, unlike Docker's inspect output.
    return subprocess.run(["docker", "logs", name], text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          check=True, timeout=10).stdout


class OptionsTest(unittest.TestCase):
    def test_options_and_existing_models(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "app/backends/onnx/models"
            source.mkdir(parents=True)
            for name in launcher.MODELS["onnx"]:
                (source / name).write_text("bundled")
            options = {"port": 8123, "confidence_threshold": 0}
            env, command = launcher.configure(options, root / "app", root / "data")
            model = Path(env["ONNX_MODEL_PATH"])
            model.write_text("preserved")
            launcher.configure(options, root / "app", root / "data")
            self.assertEqual(model.read_text(), "preserved")
            self.assertEqual(env["ONNX_CONFIDENCE_THRESHOLD"], "0")
            self.assertEqual(json.loads(env["AVAILABLE_BACKENDS"]), ["onnx"])
            self.assertEqual(command[-3:], ["127.0.0.1", "--port", "8123"])

    def test_invalid_options_fail_before_start(self):
        for options in ({"port": 0}, {"port": True}, {"default_backend": "bad"},
                        {"confidence_threshold": 2}, {"bind_address": "bad"}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                launcher.configure(options)


class DetectorContainerTest(unittest.TestCase):
    def setUp(self):
        self.name = "detect-test-" + uuid.uuid4().hex[:12]
        self.volume = self.name + "-data"
        docker("volume", "create", self.volume)

    def tearDown(self):
        docker("rm", "-f", "-v", self.name, check=False)
        docker("volume", "rm", self.volume, check=False)

    def options(self, backend):
        options = json.dumps({"default_backend": backend, "port": 8123})
        docker("run", "--rm", "--network", "none", "-v", self.volume + ":/data",
               "--entrypoint", "python", IMAGE, "-c",
               "from pathlib import Path; Path('/data/options.json').write_text(" + repr(options) + ")")

    def start(self):
        docker("run", "-d", "--name", self.name, "--network", "none",
               "-v", self.volume + ":/data", IMAGE)
        for _ in range(60):
            state = json.loads(docker("inspect", self.name))[0]["State"]
            if not state["Running"]:
                self.fail(logs(self.name))
            result = docker("exec", self.name, "curl", "-fsS",
                            "http://127.0.0.1:8123/health", check=False)
            if result:
                return
            time.sleep(1)
        self.fail("Startup timed out: " + logs(self.name))

    def check_inference(self, backend):
        self.options(backend)
        self.start()
        docker("exec", self.name, "python", "/app/healthcheck.py")
        info = json.loads(docker("exec", self.name, "curl", "-fsS",
                                 "http://127.0.0.1:8123/api/v1/backends"))
        self.assertEqual(info["default_backend"], backend)
        self.assertEqual(info["backends"][backend]["status"], "available")
        response = json.loads(docker("exec", self.name, "curl", "-fsS",
            "-F", "file=@/app/test_image.jpg", "http://127.0.0.1:8123/api/v1/detect"))
        self.assertEqual(response["backend"], backend)
        self.assertIsInstance(response["detections"], list)
        self.assertGreater(response["image_width"], 0)
        docker("exec", self.name, "sh", "-ec", "echo persistent > /data/models/sentinel")
        docker("stop", "-t", "10", self.name)
        docker("rm", "-v", self.name)
        self.start()
        self.assertEqual(docker("exec", self.name, "cat", "/data/models/sentinel"), "persistent")

    def test_onnx_inference_and_recreation(self):
        self.check_inference("onnx")

    def test_tflite_inference_and_recreation(self):
        self.check_inference("tflite")

    def test_coral_runtime_and_missing_device(self):
        docker("run", "--rm", "--network", "none", "--entrypoint", "python", IMAGE,
               "-c", "import ctypes; ctypes.CDLL('libedgetpu.so.1')")
        self.options("edgetpu")
        docker("run", "-d", "--name", self.name, "--network", "none",
               "-v", self.volume + ":/data", IMAGE)
        for _ in range(30):
            state = json.loads(docker("inspect", self.name))[0]["State"]
            if not state["Running"]:
                self.assertNotEqual(state["ExitCode"], 0)
                self.assertIn("Application startup failed", logs(self.name))
                return
            time.sleep(1)
        self.fail("Missing Coral must fail startup, not expose a healthy API")


if __name__ == "__main__":
    unittest.main(verbosity=2)
