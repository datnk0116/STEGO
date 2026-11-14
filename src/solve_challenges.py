#!/usr/bin/env python3
"""Decode the two selected CTF artifacts using independently implemented logic.

Blue 3: infer candidate flag length from the dominant RGB color and sum per
character's diagonal region, then validate the complete BYUCTF flag format.
Sleepy Alarm: extract the 8 kHz carrier envelope and decode 50-baud ASK symbols.
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.signal import butter, sosfiltfilt, hilbert
import soundfile as sf
from audio_alignment import align_reference

BLUE_RE = re.compile(r"byuctf\{[0-9A-Za-z_]*\}\Z")

def solve_blue(path: Path, max_len: int | None = None, base_color: tuple[int, int, int] | None = None) -> tuple[str | None, list[tuple[int, str]]]:
    with Image.open(path) as im:
        pixels = np.asarray(im.convert("RGB"), dtype=np.int16)
    h, w, _ = pixels.shape
    # In black-box mode, infer the cover color as the modal RGB triplet.
    # The source-informed mode accepts an explicit baseline for comparison.
    if base_color is None:
        colors, counts = np.unique(
            pixels.reshape(-1, 3), axis=0, return_counts=True
        )
        base_color = tuple(int(v) for v in colors[int(np.argmax(counts))])
    base = np.asarray(base_color, dtype=np.int16)
    limit = min(max_len or min(w, h), min(w, h))
    attempts = []
    for length in range(2, limit + 1):
        cell_w, cell_h = w // length, h // length
        chars = []
        for index in range(length):
            x0, x1 = cell_w * index, cell_w * (index + 1)
            y0, y1 = cell_h * index, cell_h * (index + 1)
            # The original generator increments one random channel by one
            # for each loop iteration. Summing channel deltas recovers ord(c).
            delta = pixels[y0:y1, x0:x1] - base
            value = int(delta.sum())
            if value < 0 or value > 0x10FFFF:
                chars = []
                break
            chars.append(chr(value))
        candidate = "".join(chars)
        if candidate:
            attempts.append((length, candidate))
        if BLUE_RE.fullmatch(candidate):
            return candidate, attempts
    return None, attempts

def _three_level_cluster(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Cluster measured ASK envelope medians into separator, zero and one levels."""
    values = np.asarray(values, dtype=np.float64)
    if values.size < 3 or not np.isfinite(values).all():
        raise ValueError("not enough finite symbol envelope measurements")
    centers = np.quantile(values, [0.05, 0.50, 0.95]).astype(np.float64)
    for _ in range(100):
        labels = np.argmin(np.abs(values[:, None] - centers[None, :]), axis=1)
        updated = centers.copy()
        for k in range(3):
            members = values[labels == k]
            if members.size:
                updated[k] = float(np.mean(members))
        updated.sort()
        if np.allclose(updated, centers, rtol=1e-7, atol=1e-12):
            centers = updated
            break
        centers = updated
    labels = np.argmin(np.abs(values[:, None] - centers[None, :]), axis=1)
    if len(np.unique(labels)) != 3:
        raise ValueError(
            "could not distinguish three ASK amplitude states; inspect the residual/envelope"
        )
    return centers, labels


def solve_sleepy(path: Path, carrier_hz: float = 8000.0,
                 baud: float = 50.0, reference: Path | None = None,
                 transmission_seconds: float = 7.0,
                 expected_text: str | None = None) -> dict:
    raw_target, sr = sf.read(path, always_2d=True, dtype="float64")
    signal = raw_target
    alignment_info = None
    if reference is not None:
        original, original_sr = sf.read(reference, always_2d=True, dtype="float64")
        aligned_target, aligned_reference, alignment_info = align_reference(
            raw_target, int(sr), original, int(original_sr)
        )
        residual = aligned_target - aligned_reference
        # The ASK payload begins at sample zero of the distributed stream.
        # Cross-correlation may crop its leading encoder-delay/preamble samples
        # because they do not overlap the original reference. Preserve those
        # target samples, then append the aligned residual. This reconstructs
        # the distributed timeline without discarding the first ASK symbols.
        if alignment_info["channel_handling"] == "downmixed_to_mono":
            raw_prefix = raw_target.mean(axis=1, keepdims=True)
        else:
            raw_prefix = raw_target
        prefix = raw_prefix[:target_start] if target_start > 0 else raw_prefix[:0]
        signal = np.concatenate((prefix, residual), axis=0)

    if not 0 < baud <= 1000:
        raise ValueError("baud must be in (0, 1000]")
    if not 0 < carrier_hz < sr / 2:
        raise ValueError(f"carrier {carrier_hz} Hz must be below Nyquist")
    low, high = carrier_hz - 500, carrier_hz + 500
    if low <= 0 or high >= sr / 2:
        raise ValueError("sample rate too low for selected carrier band")

    # The official MATLAB generator adds ASK to the first/left channel only.
    # Do not average stereo channels: doing so halves the signal amplitude.
    analysis_channel = 0
    channel_signal = signal[:, analysis_channel]

    samples_per_bit = sr / baud
    symbol_count = int(round(transmission_seconds * baud))
    phase_offset = 0

    # Coherent per-symbol amplitude detection. Each 50-baud symbol contains
    # exactly 160 carrier cycles at 8 kHz when fs=44.1 kHz. Project each
    # 882-sample block onto sine/cosine bases at the known carrier; this avoids
    # the Hilbert/filter edge transient that corrupted the first symbols.
    levels = []
    for i in range(symbol_count):
        bit_start = int(round(phase_offset + i * samples_per_bit))
        bit_end = int(round(phase_offset + (i + 1) * samples_per_bit))
        if bit_end > len(channel_signal):
            break
        segment = channel_signal[bit_start:bit_end].astype(np.float64, copy=False)
        if segment.size < 8:
            break
        sample_index = np.arange(bit_start, bit_end, dtype=np.float64)
        phase = 2.0 * np.pi * carrier_hz * sample_index / sr
        # Remove DC only; the sine/cosine projection rejects components not
        # coherent with the 8 kHz carrier over the full symbol window.
        segment = segment - float(np.mean(segment))
        in_phase = (2.0 / segment.size) * float(np.dot(segment, np.cos(phase)))
        quadrature = (2.0 / segment.size) * float(np.dot(segment, np.sin(phase)))
        levels.append(float(np.hypot(in_phase, quadrature)))
    if len(levels) != symbol_count:
        raise ValueError(
            f"expected {symbol_count} symbols for {transmission_seconds}s at {baud} baud, "
            f"but only measured {len(levels)}; check alignment and source duration"
        )

    centers, labels = _three_level_cluster(np.asarray(levels))
    # Source documents three states: 0 amplitude = byte separator,
    # 2e-3 = bit 0, 5e-3 = bit 1. The three clusters are ordered by amplitude.
    mapping = {0: " ", 1: "0", 2: "1"}
    symbols = [mapping[int(label)] for label in labels]
    chunks = []
    current = []
    for symbol in symbols:
        if symbol == " ":
            if current:
                chunks.append("".join(current))
                current = []
        else:
            current.append(symbol)
    if current:
        chunks.append("".join(current))

    decoded = []
    errors = []
    for idx, chunk in enumerate(chunks):
        if len(chunk) != 8:
            errors.append({"index": idx, "bits": chunk, "reason": "not an 8-bit byte"})
            continue
        decoded.append(chr(int(chunk, 2)))
    decoded_text = "".join(decoded)
    expected_prefix_ok = decoded_text.startswith("ictf{")
    expected_suffix_ok = decoded_text.endswith("}")
    if expected_text is not None and (
        len(expected_text) != 39 or not expected_text.startswith("ictf{")
        or not expected_text.endswith("}")
    ):
        raise ValueError("--expected must be a 39-character ictf{...} flag")
    format_valid = (
        len(chunks) == 39 and not errors and len(decoded_text) == 39
        and expected_prefix_ok and expected_suffix_ok
    )
    ground_truth_match = (
        decoded_text == expected_text if expected_text is not None else None
    )
    return {
        "samplerate_hz": int(sr),
        "channels": int(signal.shape[1]),
        "analysis_channel": analysis_channel,
        "carrier_hz": carrier_hz,
        "baud": baud,
        "samples_per_bit": samples_per_bit,
        "transmission_seconds": transmission_seconds,
        "expected_symbol_count": symbol_count,
        "measured_symbol_count": len(levels),
        "symbol_clock_phase_samples_after_alignment": phase_offset,
        "reference_alignment": alignment_info,
        "alignment_interpretation": (
            "Preserved the unaligned distributed-stream prefix, then appended the aligned residual to restore the complete ASK timeline."
            if alignment_info else "No reference alignment was requested."
        ),
        "preserved_prefix_samples": (
            int(alignment_info["target_start_sample"]) if alignment_info else 0
        ),
        "amplitude_measurement": "coherent sine/cosine projection per symbol",
        "amplitude_cluster_centers": [float(x) for x in centers],
        "symbol_amplitude_estimates": [float(x) for x in levels],
        "symbol_labels": symbols,
        "symbol_counts": {
            "separator": symbols.count(" "),
            "bit_0": symbols.count("0"),
            "bit_1": symbols.count("1"),
        },
        "byte_count": len(chunks),
        "decoded_text": decoded_text,
        "expected_flag_length": 39,
        "decoded_length": len(decoded_text),
        "flag_prefix_ok": expected_prefix_ok,
        "flag_suffix_ok": expected_suffix_ok,
        "format_valid": format_valid,
        "expected_text_provided": expected_text is not None,
        "ground_truth_match": ground_truth_match,
        "decoded_utf8_hex": decoded_text.encode("utf-8", errors="replace").hex(),
        "errors": errors,
        "success": (
            bool(format_valid and ground_truth_match)
            if expected_text is not None else None
        ),
        "note": (
            "The amplitude clusters are estimated from the measured residual. "
            "Confirm cluster centers are consistent with the documented 0/0.002/0.005 states."
        ),
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="challenge", required=True)
    b = sub.add_parser("blue3")
    b.add_argument("image", type=Path)
    b.add_argument("--max-len", type=int)
    b.add_argument("--base-color", type=int, nargs=3, default=None, metavar=("R", "G", "B"), help="Optional source-informed baseline; omit to infer the modal RGB color")
    a = sub.add_parser("sleepy-alarm")
    a.add_argument("audio", type=Path)
    a.add_argument("--carrier", type=float, default=8000.0)
    a.add_argument("--baud", type=float, default=50.0)
    a.add_argument("--transmission-seconds", type=float, default=7.0)
    a.add_argument("--reference", type=Path, help="Optional original audio; resample and align before subtraction")
    a.add_argument("--expected", type=str, help="Optional exact ground-truth flag for independent verification")
    args = parser.parse_args()
    if args.challenge == "blue3":
        result, attempts = solve_blue(
            args.image, args.max_len,
            tuple(args.base_color) if args.base_color is not None else None
        )
        print("Candidate:", result if result else "NOT FOUND")
        print("Attempts:", len(attempts))
        if result:
            print("Format validated:", bool(BLUE_RE.fullmatch(result)))
            return 0
        return 2
    import json
    result = solve_sleepy(
        args.audio, args.carrier, args.baud,
        reference=args.reference,
        transmission_seconds=args.transmission_seconds,
        expected_text=args.expected,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["format_valid"]:
        return 2
    if args.expected is not None and not result["ground_truth_match"]:
        return 3
    return 0
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
