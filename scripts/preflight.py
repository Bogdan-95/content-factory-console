# авто-скачивание моделей

import hashlib
import json
import os
import sys
from pathlib import Path
import urllib.request

ROOT = Path("/opt/ComfyUI/models")
MAP = Path(os.environ.get("MODELS_MAP", "/app/models_map.json"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".part")
    print(f"↓ {url} -> {dst}", flush=True)
    urllib.request.urlretrieve(url, tmp)
    tmp.rename(dst)


def main() -> int:
    spec = json.loads(MAP.read_text(encoding="utf-8"))
    for _grop, items in spec.items():
        for item in items:
            dst = ROOT / item["dest"]
            if dst.exists():
                if "sha256" in item and sha256(dst) != item["sha256"]:
                    print(f"! checksum mismatch for {dst}, redownloading", flush=True)
                    dst.unlink()
                else:
                    print(f"✓ {dst}", flush=True)
                    continue
            download(item["url"], dst)
            if "sha256" in item and sha256(dst) != item["sha256"]:
                print(f"✗ checksum FAILED for {dst}", flush=True)
                return 2
    print("✅ preflight: all models ready", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
