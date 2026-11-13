#!/usr/bin/env python3
"""Decode the two selected CTF artifacts using independently implemented logic.

Blue 3: infer candidate flag length from the dominant RGB color and sum per
character's diagonal region, then validate the complete BYUCTF flag format.
Sleepy Alarm: extract the 8 kHz carrier envelope and decode 50-baud ASK symbols.
"""
from __future__ import annotations
import argparse
import re
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.signal import butter, sosfiltfilt, hilbert
import soundfile as sf

BLUE_RE = re.compile(r"byuctf\{[0-9A-Za-z_]*\}\Z")

def solve_blue(path: Path, max_len: int | None = None, base_color: tuple[int, int, int] = (64, 77, 205)) -> tuple[str | None, list[tuple[int, str]]]:
    with Image.open(path) as im:
        pixels = np.asarray(im.convert("RGB"), dtype=np.int16)
    h, w, _ = pixels.shape
    # Blue 3's official creator uses a flat RGB (64,77,205) cover. Using
    # that known baseline avoids depending on modal-color assumptions.
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

def solve_sleepy(path: Path, carrier_hz: float = 8000.0,
                 baud: float = 50.0, zero_amp: float = 2e-3,
                 one_amp: float = 5e-3, stop_amp: float = 0.0,
                 reference: Path | None = None) -> dict:
    signal, sr = sf.read(path, always_2d=True, dtype="float64")
    if reference is not None:
        original, original_sr = sf.read(reference, always_2d=True, dtype="float64")
        if original_sr != sr or original.shape != signal.shape:
            raise ValueError("reference must match sample rate, frame count and channel count")
        signal = signal - original
    # Mono average retains an in-phase carrier; report when a stereo mix might
    # cancel content and allow explicit manual channel inspection if needed.
    mono = signal.mean(axis=1)
    nyquist = sr / 2
    if not 0 < baud <= 1000:
        raise ValueError("baud must be in (0, 1000]")
    if not 0 < carrier_hz < nyquist:
        raise ValueError(f"carrier {carrier_hz} Hz must be below Nyquist ({nyquist} Hz)")
    # A narrow bandpass around the documented carrier; envelope removes carrier phase.
    low, high = carrier_hz - 500, carrier_hz + 500
    if low <= 0 or high >= nyquist:
        raise ValueError("sample rate too low for the selected carrier band")
    sos = butter(4, [low, high], btype="bandpass", fs=sr, output="sos")
    band = sosfiltfilt(sos, mono)
    envelope = np.abs(hilbert(band))
    samples_per_bit = sr / baud
    # 0.02 s symbols are 882 samples at 44.1 kHz. Use centers to avoid transitions.
    nbits = int(len(envelope) / samples_per_bit)
    symbols = []
    values = []
    for i in range(nbits):
        start = int(round(i * samples_per_bit + samples_per_bit * 0.25))
        end = int(round((i + 1) * samples_per_bit - samples_per_bit * 0.25))
        if end <= start:
            continue
        level = float(np.median(envelope[start:end]))
        values.append(level)
        if abs(level - zero_amp) <= abs(level - one_amp) and abs(level-zero_amp) < zero_amp*0.8:
            symbols.append("0")
        elif abs(level - one_amp) < one_amp*0.8:
            symbols.append("1")
        elif level < max(zero_amp, one_amp) * 0.2:
            symbols.append(" ")
        else:
            symbols.append("?")
    # The source describes a zero-amplitude symbol as a byte separator/completion.
    # Strip leading/trailing separators and decode each 8-bit group.
    bitstream = "".join(symbols).strip()
    chunks = [x for x in bitstream.split() if x]
    decoded = []
    errors = []
    for idx, chunk in enumerate(chunks):
        if len(chunk) != 8 or set(chunk) - {"0", "1"}:
            errors.append({"index": idx, "bits": chunk, "reason": "not an 8-bit byte"})
            continue
        decoded.append(chr(int(chunk, 2)))
    return {
        "samplerate_hz": sr, "channels": signal.shape[1],
        "duration_seconds": len(mono)/sr, "carrier_hz": carrier_hz,
        "baud": baud, "samples_per_bit": samples_per_bit,
        "symbol_count": len(symbols), "separator_count": symbols.count(" "),
        "unknown_symbol_count": symbols.count("?"),
        "median_envelope_range": [float(np.min(values)), float(np.max(values))] if values else None,
        "bit_chunks": chunks, "decoded_text": "".join(decoded), "errors": errors,
        "note": "Exploratory ASK envelope decoder. Verify against original challenge source and test timing/threshold sensitivity."
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="challenge", required=True)
    b = sub.add_parser("blue3")
    b.add_argument("image", type=Path)
    b.add_argument("--max-len", type=int)
    b.add_argument("--base-color", type=int, nargs=3, default=(64, 77, 205), metavar=("R", "G", "B"))
    a = sub.add_parser("sleepy-alarm")
    a.add_argument("audio", type=Path)
    a.add_argument("--carrier", type=float, default=8000.0)
    a.add_argument("--baud", type=float, default=50.0)
    a.add_argument("--reference", type=Path, help="Optional aligned original audio; analyze residual only")
    args = parser.parse_args()
    if args.challenge == "blue3":
        result, attempts = solve_blue(args.image, args.max_len, tuple(args.base_color))
        print("Candidate:", result if result else "NOT FOUND")
        print("Attempts:", len(attempts))
        if result:
            print("Format validated:", bool(BLUE_RE.fullmatch(result)))
            return 0
        return 2
    import json
    print(json.dumps(solve_sleepy(args.audio, args.carrier, args.baud, reference=args.reference), indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
