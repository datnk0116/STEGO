#!/usr/bin/env python3
"""Measure Sleepy Alarm robustness when only target OR reference is transformed.

The official artifacts are read-only. Each trial writes temporary WAV copies,
then reruns the same reference-assisted decoder and records exact-match status.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from solve_challenges import solve_sleepy


def _roundtrip(array: np.ndarray, sample_rate: int) -> np.ndarray:
    up = resample_poly(array, 48000, sample_rate, axis=0)
    return resample_poly(up, sample_rate, 48000, axis=0)


def _write_pair(directory: Path, name: str, target: np.ndarray,
                target_sr: int, reference: np.ndarray, reference_sr: int):
    target_path = directory / f"{name}_target.wav"
    reference_path = directory / f"{name}_reference.wav"
    sf.write(target_path, target, target_sr, subtype="PCM_24")
    sf.write(reference_path, reference, reference_sr, subtype="PCM_24")
    return target_path, reference_path


def _evaluate(name: str, target_path: Path, reference_path: Path,
              expected: str, target_clip: float = 0.0,
              reference_clip: float = 0.0) -> dict:
    started = time.perf_counter()
    result = solve_sleepy(target_path, reference=reference_path,
                          expected_text=expected)
    return {
        "variant": name,
        "success": bool(result["success"]),
        "format_valid": bool(result["format_valid"]),
        "ground_truth_match": result["ground_truth_match"],
        "decoded_length": result["decoded_length"],
        "symbol_count": result["measured_symbol_count"],
        "separator_count": result["symbol_counts"]["separator"],
        "errors": result["errors"],
        "alignment_lag_samples": result["reference_alignment"]["alignment_lag_samples"],
        "alignment_correlation": result["reference_alignment"]["normalized_abs_correlation"],
        "target_clipped_fraction": target_clip,
        "reference_clipped_fraction": reference_clip,
        "elapsed_seconds": time.perf_counter() - started,
        "decoded_text": result["decoded_text"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--out-dir", type=Path,
                        default=Path("results/sleepy_alarm/asymmetric_robustness"))
    args = parser.parse_args()
    if not args.audio.is_file() or not args.reference.is_file():
        parser.error("both distributed audio and reference audio must exist")

    target, target_sr = sf.read(args.audio, always_2d=True, dtype="float64")
    reference, reference_sr = sf.read(args.reference, always_2d=True, dtype="float64")
    if target.size == 0 or reference.size == 0:
        parser.error("audio inputs must not be empty")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    baseline = _evaluate("baseline", args.audio, args.reference, args.expected)
    rows.append(baseline)
    if not baseline["success"]:
        result = {
            "baseline_success": False,
            "results": rows,
            "note": "Asymmetric trials skipped because the official baseline did not exact-match.",
        }
        (args.out_dir / "asymmetric_robustness.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 2

    with tempfile.TemporaryDirectory(prefix="sleepy-asymmetric-") as temp:
        temp_dir = Path(temp)
        for side in ("target", "reference"):
            for gain in (0.5, 1.5):
                t = target.copy()
                r = reference.copy()
                if side == "target":
                    raw = t * gain
                    t = np.clip(raw, -1.0, 1.0)
                    t_clip = float(np.mean(np.abs(raw) >= 1.0))
                    r_clip = 0.0
                else:
                    raw = r * gain
                    r = np.clip(raw, -1.0, 1.0)
                    r_clip = float(np.mean(np.abs(raw) >= 1.0))
                    t_clip = 0.0
                tp, rp = _write_pair(
                    temp_dir, f"{side}_gain_{gain}", t, int(target_sr),
                    r, int(reference_sr))
                rows.append(_evaluate(
                    f"{side}_only_gain_{gain}", tp, rp, args.expected,
                    t_clip, r_clip))

            t = _roundtrip(target, int(target_sr)) if side == "target" else target
            r = _roundtrip(reference, int(reference_sr)) if side == "reference" else reference
            tp, rp = _write_pair(
                temp_dir, f"{side}_only_resample_roundtrip", t, int(target_sr),
                r, int(reference_sr))
            rows.append(_evaluate(
                f"{side}_only_resample_44k1_48k_44k1",
                tp, rp, args.expected))

    csv_path = args.out_dir / "asymmetric_robustness.csv"
    fields = list(rows[0].keys())
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "baseline_success": True,
        "all_variants_success": all(row["success"] for row in rows),
        "success_count": sum(row["success"] for row in rows),
        "variant_count": len(rows) - 1,
        "results": rows,
        "csv": str(csv_path),
        "interpretation": (
            "Each transform is applied to only one side of the target/reference pair. "
            "Results characterize this decoder and these exact transformations only."
        ),
    }
    (args.out_dir / "asymmetric_robustness.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
