#!/usr/bin/env python3
"""One-sided audio robustness matrix with symbol and bit-error measurements."""
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
from scipy.signal import butter, resample_poly, sosfiltfilt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "experiments"))
from solve_challenges import solve_sleepy
from robustness_metrics import sleepy_symbol_metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--expected", required=True,
                        help="Ground truth used only to score the measured symbol stream")
    parser.add_argument("--out", type=Path, default=Path("results/sleepy_alarm/robustness_matrix"))
    parser.add_argument("--seed", type=int, default=20261114)
    args = parser.parse_args()

    for path in (args.audio, args.reference):
        if not path.is_file():
            parser.error(f"missing audio file: {path}")
    target, sample_rate = sf.read(args.audio, always_2d=True, dtype="float64")
    reference, reference_sr = sf.read(args.reference, always_2d=True, dtype="float64")
    if sample_rate != reference_sr:
        raise ValueError("target/reference sample rates must match for this matrix")

    args.out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    rows = []

    def evaluate(name: str, transformed_target: np.ndarray,
                 transformed_reference: np.ndarray, side: str) -> None:
        with tempfile.TemporaryDirectory(prefix="ask-matrix-") as temporary:
            temp_dir = Path(temporary)
            target_path = temp_dir / "target.wav"
            reference_path = temp_dir / "reference.wav"
            sf.write(target_path, transformed_target, sample_rate)
            sf.write(reference_path, transformed_reference, reference_sr)

            started = time.perf_counter()
            result = solve_sleepy(
                target_path, reference=reference_path, expected_text=args.expected
            )
            elapsed = time.perf_counter() - started

        recovery = sleepy_symbol_metrics(args.expected, result["symbol_labels"])
        rows.append({
            "variant": name,
            "transformed_side": side,
            "success": result["success"],
            "format_valid": result["format_valid"],
            "decoded_length": result["decoded_length"],
            "symbols": result["measured_symbol_count"],
            "separators": result["symbol_counts"]["separator"],
            "errors": json.dumps(result["errors"]),
            "alignment_correlation": result["reference_alignment"]["normalized_abs_correlation"],
            "elapsed_seconds": elapsed,
            "decoded_text": result["decoded_text"],
            **recovery,
        })

    evaluate("baseline", target, reference, "none")
    for side in ("target", "reference"):
        base = target if side == "target" else reference
        for gain in (0.25, 0.5, 0.75, 1.25, 1.5, 1.75):
            changed = np.clip(base * gain, -1, 1)
            evaluate(
                f"{side}_gain_{gain}",
                changed if side == "target" else target,
                changed if side == "reference" else reference,
                side,
            )
        for snr_db in (30, 20, 10):
            power = float(np.mean(base ** 2))
            noise_power = power / (10 ** (snr_db / 10))
            changed = base + rng.normal(0, np.sqrt(noise_power), base.shape)
            evaluate(
                f"{side}_awgn_snr_{snr_db}db",
                changed if side == "target" else target,
                changed if side == "reference" else reference,
                side,
            )
        sos = butter(4, [7500, 8500], btype="bandpass", fs=sample_rate, output="sos")
        changed = sosfiltfilt(sos, base, axis=0)
        evaluate(
            f"{side}_bandpass_7p5_8p5khz",
            changed if side == "target" else target,
            changed if side == "reference" else reference,
            side,
        )
        changed = resample_poly(base, 160, 147, axis=0)
        changed = resample_poly(changed, 147, 160, axis=0)[:len(base)]
        evaluate(
            f"{side}_resample_roundtrip_44k1_48k",
            changed if side == "target" else target,
            changed if side == "reference" else reference,
            side,
        )

    csv_path = args.out / "robustness_matrix.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    result = {
        "seed": args.seed,
        "trial_count": len(rows),
        "pass_count": sum(bool(row["success"]) for row in rows),
        "partial_recovery_note": (
            "BER and separator precision/recall compare measured symbols with the "
            "ground-truth encoding only after extraction; expected text is not an input "
            "to the decoder."
        ),
        "aggregate": {
            "mean_symbol_error_rate": float(np.mean([row["symbol_error_rate"] for row in rows])),
            "mean_bit_error_rate": float(np.mean([row["bit_error_rate"] for row in rows])),
            "mean_separator_precision": float(np.mean([
                row["separator_precision"] for row in rows
                if row["separator_precision"] is not None
            ])),
            "mean_separator_recall": float(np.mean([
                row["separator_recall"] for row in rows
                if row["separator_recall"] is not None
            ])),
        },
        "results": rows,
        "warning": "Single-artifact exploratory matrix; not a population-level robustness estimate.",
        "csv": str(csv_path),
    }
    (args.out / "robustness_matrix.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "trial_count": result["trial_count"],
        "pass_count": result["pass_count"],
        "mean_bit_error_rate": result["aggregate"]["mean_bit_error_rate"],
        "mean_symbol_error_rate": result["aggregate"]["mean_symbol_error_rate"],
        "csv": str(csv_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
