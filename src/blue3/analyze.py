#!/usr/bin/env python3
"""Reproducible, non-destructive image triage for the Blue 3 artifact."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("image", type=Path)
    p.add_argument("--reference", type=Path, help="Optional aligned cover/reference image")
    p.add_argument("--output", type=Path, help="Optional JSON output path")
    args = p.parse_args()
    if not args.image.is_file():
        p.error(f"image does not exist: {args.image}")
    with Image.open(args.image) as im:
        info = {
            "file": str(args.image),
            "sha256": sha256(args.image),
            "format": im.format,
            "mode": im.mode,
            "size": list(im.size),
            "metadata_keys": sorted(map(str, im.info.keys())),
        }
        arr = np.asarray(im.convert("RGB"), dtype=np.int16)
    info["pixel_count"] = int(arr.shape[0] * arr.shape[1])
    info["channels"] = {}
    for idx, name in enumerate(("R", "G", "B")):
        channel = arr[:, :, idx]
        hist = np.bincount(channel.astype(np.uint8).ravel(), minlength=256)
        info["channels"][name] = {
            "min": int(channel.min()),
            "max": int(channel.max()),
            "mean": float(channel.mean()),
            "std": float(channel.std()),
            "unique_values": int(np.unique(channel).size),
            "histogram_nonzero_bins": int(np.count_nonzero(hist)),
        }
    if args.reference:
        if not args.reference.is_file():
            p.error(f"reference image does not exist: {args.reference}")
        with Image.open(args.reference) as ref:
            ref_arr = np.asarray(ref.convert("RGB"), dtype=np.int16)
            info["reference"] = {
                "file": str(args.reference),
                "sha256": sha256(args.reference),
                "size": list(ref.size),
            }
        if ref_arr.shape != arr.shape:
            p.error("reference must have the same dimensions after RGB conversion")
        diff = np.abs(arr - ref_arr)
        info["difference"] = {
            "changed_channel_samples": int(np.count_nonzero(diff)),
            "total_channel_samples": int(diff.size),
            "changed_fraction": float(np.count_nonzero(diff) / diff.size),
            "mean_absolute_difference": float(diff.mean()),
            "max_absolute_difference": int(diff.max()),
        }
    text = json.dumps(info, indent=2, ensure_ascii=False)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
