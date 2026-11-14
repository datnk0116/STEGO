#!/usr/bin/env python3
"""Extended Blue 3 attack matrix with exact and partial character recovery metrics."""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "experiments"))
from solve_challenges import solve_blue
from robustness_metrics import blue_character_metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--out", type=Path, default=Path("results/blue3/extended_robustness"))
    parser.add_argument("--seed", type=int, default=20261114)
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error(f"missing image: {args.image}")

    args.out.mkdir(parents=True, exist_ok=True)
    with Image.open(args.image) as image:
        original = image.convert("RGB")

    baseline, _ = solve_blue(args.image)
    if not baseline:
        raise RuntimeError("baseline did not decode")
    expected_length = len(baseline)

    rng = np.random.default_rng(args.seed)
    variants = {
        "brightness_0.9": ImageEnhance.Brightness(original).enhance(0.9),
        "brightness_1.1": ImageEnhance.Brightness(original).enhance(1.1),
        "contrast_0.9": ImageEnhance.Contrast(original).enhance(0.9),
        "contrast_1.1": ImageEnhance.Contrast(original).enhance(1.1),
        "gaussian_blur_radius_0.3": original.filter(ImageFilter.GaussianBlur(0.3)),
        "crop_16px": original.crop((16, 16, original.width - 16, original.height - 16)),
    }
    array = np.asarray(original, dtype=np.int16)
    for sigma in (0.5, 1.0, 2.0):
        variants[f"gaussian_noise_sigma_{sigma}"] = Image.fromarray(
            np.clip(array + rng.normal(0, sigma, array.shape), 0, 255).astype(np.uint8)
        )

    rows = []
    for name, image in variants.items():
        path = args.out / f"{name}.png"
        image.save(path)
        started = time.perf_counter()
        candidate, attempts = solve_blue(path)
        elapsed = time.perf_counter() - started

        candidate_at_expected_length = next(
            (text for length, text in attempts if length == expected_length),
            candidate if candidate and len(candidate) == expected_length else None,
        )
        partial = blue_character_metrics(baseline, candidate_at_expected_length)
        rows.append({
            "variant": name,
            "success": candidate == baseline,
            "candidate": candidate,
            "candidate_at_expected_length": candidate_at_expected_length,
            **partial,
            "attempts": len(attempts),
            "elapsed_seconds": elapsed,
        })

    csv_path = args.out / "extended_robustness.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    result = {
        "baseline_success": True,
        "baseline_length": expected_length,
        "seed": args.seed,
        "variant_count": len(rows),
        "success_count": sum(row["success"] for row in rows),
        "partial_recovery_note": (
            "Character metrics use the candidate at the baseline flag length. "
            "A missing candidate is reported as unavailable, not as a measured edit distance."
        ),
        "results": rows,
        "warning": "Results characterize this decoder and exact attack settings only.",
        "csv": str(csv_path),
    }
    (args.out / "extended_robustness.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
