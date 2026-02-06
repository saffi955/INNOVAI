import os
import shutil
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
COLLECTED = BASE / "collected"


def ensure_dir(path):
    path.parent.mkdir(parents=True, exist_ok=True)


def assemble(manifest_path="manifest.json"):
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    items = manifest.get("items", [])
    COLLECTED.mkdir(parents=True, exist_ok=True)

    for it in items:
        src = Path(it["src"])
        dst = BASE / it["dst"]
        ensure_dir(dst)
        if not src.exists():
            print(f"WARNING: source not found: {src}")
            continue
        try:
            shutil.copy2(src, dst)
            print(f"Copied: {src} -> {dst}")
        except Exception as e:
            print(f"ERROR copying {src} -> {dst}: {e}")


if __name__ == "__main__":
    print("Assembling project files into 'collected/' folder...")
    assemble()
    print("Done. Check the 'collected/' folder.")
