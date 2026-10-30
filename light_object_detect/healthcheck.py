from pathlib import Path
from urllib.request import urlopen

port = int(Path("/run/light-object-detect.port").read_text())
with urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as response:
    if response.status != 200:
        raise SystemExit(1)
