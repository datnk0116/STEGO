#!/usr/bin/env python3
"""Run paired, reproducible robustness tests for the Sleepy Alarm ASK decoder."""
from __future__ import annotations
import argparse
import csv
import json
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from pathlib import Path as _Path
import sys
sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from solve_challenges import solve_sleepy

def _write_pair(directory: Path, name: str, target: np.ndarray,
                target_sr: int, reference: np.ndarray, reference_sr: int):
    target_path = directory / f"{name}_target.wav"
    reference_path = directory / f"{name}_reference.wav"
    sf.write(target_path, target, target_sr, subtype="PCM_24")
    sf.write(reference_path, reference, reference_sr, subtype="PCM_24")
    return target_path, reference_path

def _evaluate(name: str, target_path: Path, reference_path: Path,
              expected: str) -> dict:
    start = time.perf_counter()
    result = solve_sleepy(target_path, reference=reference_path,
                          expected_text=expected)
    elapsed = time.perf_counter() - start
    return {
        "variant": name,
        "success": bool(result["success"]),
        "format_valid": bool(result["format_valid"]),
        "ground_truth_match": result["ground_truth_match"],
        "decoded_length": result["decoded_length"],
        "symbol_count": result["measured_symbol_count"],
        "separator_count": result["symbol_counts"]["separator"],
        "cluster_centers": result["amplitude_cluster_centers"],
        "alignment_lag_samples": result["reference_alignment"]["alignment_lag_samples"],
        "alignment_correlation": result["reference_alignment"]["normalized_abs_correlation"],
        "errors": result["errors"],
        "elapsed_seconds": elapsed,
        "decoded_text": result["decoded_text"],
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("results/sleepy_alarm/robustness"))
    args = parser.parse_args()
    if not args.audio.is_file() or not args.reference.is_file():
        parser.error("both distributed audio and reference audio must exist")

    target, sr = sf.read(args.audio, always_2d=True, dtype="float64")
    reference, ref_sr = sf.read(args.reference, always_2d=True, dtype="float64")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    # Baseline directly from official distributed and reference MP3 files.
    baseline = _evaluate("original_mp3", args.audio, args.reference, args.expected)
    rows.append(baseline)
    if not baseline["success"]:
        result = {"baseline_success": False, "results": rows,
                  "note": "Robustness trials skipped because the official MP3 baseline did not decode exactly."}
        (args.out_dir / "sleepy_alarm_robustness.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 2

    with tempfile.TemporaryDirectory(prefix="sleepy-robustness-") as temp:
        temp_dir = Path(temp)

        # Paired resample round trip, preserving the same operation on carrier
        # and reference so the comparison is not biased by a mismatched path.
        converted = []
        for array, rate in ((target, sr), (reference, ref_sr)):
            to_48 = resample_poly(array, 48000, int(rate), axis=0)
            back = resample_poly(to_48, int(rate), 48000, axis=0)
            converted.append(back)
        target_rt = converted[0]
        reference_rt = converted[1]
        t_path, r_path = _write_pair(
            temp_dir, "resample_roundtrip", target_rt, int(sr),
            reference_rt, int(ref_sr)
        )
        rows.append(_evaluate("resample_44k1_48k_44k1", t_path, r_path, args.expected))

        # Apply gain to both sides. 1.5x includes clipping if the waveform
        # exceeds full scale; the actual clipped-sample fraction is recorded.
        for gain in (0.5, 1.5):
            target_gain = np.clip(target * gain, -1.0, 1.0)
            ref_gain = np.clip(reference * gain, -1.0, 1.0)
            t_path, r_path = _write_pair(
                temp_dir, f"gain_{gain}", target_gain, int(sr),
                ref_gain, int(ref_sr)
            )
            row = _evaluate(f"paired_gain_{gain}", t_path, r_path, args.expected)
            row["target_clipped_fraction"] = float(np.mean(np.abs(target * gain) >= 1.0))
            row["reference_clipped_fraction"] = float(np.mean(np.abs(reference * gain) >= 1.0))
            rows.append(row)

    fieldnames = sorted({key for row in rows for key in row})
    csv_path = args.out_dir / "sleepy_alarm_robustness.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                for key, value in row.items()
            })
    result = {
        "baseline_success": True,
        "all_variants_success": all(row["success"] for row in rows),
        "results": rows,
        "csv": str(csv_path),
        "interpretation": (
            "A failure after a transform is evidence of sensitivity for this challenge and decoder only; "
            "it is not a universal claim about audio steganography."
        ),
    }
    (args.out_dir / "sleepy_alarm_robustness.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
