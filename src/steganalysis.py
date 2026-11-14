#!/usr/bin/env python3
"""Explainable first-pass steganalysis features for the two studied carriers.

This is a challenge-oriented triage baseline, not a universal steganography detector.
Thresholds are explicit heuristics and must be evaluated on held-out corpora.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
from PIL import Image
import soundfile as sf
from scipy.signal import periodogram


def image_features(path: Path) -> dict:
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    flat = rgb.reshape(-1, 3)
    _, counts = np.unique(flat, axis=0, return_counts=True)
    modal_fraction = float(counts.max() / flat.shape[0])
    channel_std = np.std(rgb.astype(np.float64), axis=(0, 1))
    # A near-uniform carrier with sparse one-level modifications is a
    # challenge-specific clue, not proof: ordinary graphics can look similar.
    return {
        "width": int(rgb.shape[1]),
        "height": int(rgb.shape[0]),
        "modal_rgb_fraction": modal_fraction,
        "mean_channel_std": float(channel_std.mean()),
        "unique_rgb_count": int(len(counts)),
    }


def audio_features(path: Path, carrier_hz: float = 8000.0,
                   baud: float = 50.0) -> dict:
    audio, sample_rate = sf.read(path, always_2d=True, dtype="float64")
    if audio.size == 0 or not np.isfinite(audio).all():
        raise ValueError("audio must contain finite samples")
    if not 0 < carrier_hz < sample_rate / 2:
        raise ValueError("carrier must be below Nyquist")
    signal = audio[:, 0]
    frequencies, power = periodogram(signal, fs=sample_rate, scaling="spectrum")
    total = float(power[(frequencies >= 100) & (frequencies < sample_rate / 2)].sum())
    band = (frequencies >= carrier_hz - 100) & (frequencies <= carrier_hz + 100)
    carrier_ratio = float(power[band].sum() / max(total, 1e-30))
    # RMS of carrier-sized blocks is a cheap, reference-free modulation proxy.
    samples_per_symbol = max(1, int(round(sample_rate / baud)))
    usable = signal[:len(signal) // samples_per_symbol * samples_per_symbol]
    if usable.size:
        blocks = usable.reshape(-1, samples_per_symbol)
        levels = np.sqrt(np.mean(blocks * blocks, axis=1))
        level_cv = float(np.std(levels) / max(float(np.mean(levels)), 1e-12))
    else:
        level_cv = 0.0
    return {
        "sample_rate_hz": int(sample_rate),
        "channels": int(audio.shape[1]),
        "duration_seconds": float(len(audio) / sample_rate),
        "carrier_band_energy_ratio": carrier_ratio,
        "symbol_block_rms_cv": level_cv,
    }


def classify_image(features: dict) -> tuple[bool, list[str]]:
    reasons = []
    if features["modal_rgb_fraction"] >= 0.90:
        reasons.append("dominant_rgb_colour_fraction>=0.90")
    if features["mean_channel_std"] <= 8.0:
        reasons.append("low_mean_channel_std<=8")
    return len(reasons) == 2, reasons


def classify_audio(features: dict) -> tuple[bool, list[str]]:
    reasons = []
    if features["carrier_band_energy_ratio"] >= 0.02:
        reasons.append("8khz_band_energy_ratio>=0.02")
    if features["symbol_block_rms_cv"] >= 0.15:
        reasons.append("50_baud_block_rms_cv>=0.15")
    return len(reasons) == 2, reasons


def analyze(path: Path, kind: str) -> dict:
    if kind == "image":
        features = image_features(path)
        flagged, reasons = classify_image(features)
    elif kind == "audio":
        features = audio_features(path)
        flagged, reasons = classify_audio(features)
    else:
        raise ValueError("kind must be image or audio")
    return {"file": str(path), "kind": kind, "flagged": flagged,
            "reasons": reasons, "features": features,
            "warning": "Heuristic triage only; not a calibrated or universal detector."}
