"""Utilities for sample-rate conversion and time alignment of reference audio."""
from __future__ import annotations
from fractions import Fraction
import numpy as np
from scipy.signal import correlate, correlation_lags, resample_poly

def _to_mono_or_match_channels(target: np.ndarray, reference: np.ndarray):
    if target.shape[1] != reference.shape[1]:
        # A channel mismatch makes per-channel subtraction invalid. A mono
        # comparison is safer and avoids silently pairing unrelated channels.
        return target.mean(axis=1, keepdims=True), reference.mean(axis=1, keepdims=True), "downmixed_to_mono"
    return target, reference, "channelwise"

def _slice_for_lag(target: np.ndarray, reference: np.ndarray, lag: int):
    # Positive lag means the target starts later than the reference.
    t0, r0 = max(lag, 0), max(-lag, 0)
    n = min(len(target) - t0, len(reference) - r0)
    if n <= 0:
        raise ValueError("reference and target have no overlapping samples")
    return target[t0:t0+n], reference[r0:r0+n], t0, r0

def align_reference(target: np.ndarray, target_sr: int,
                    reference: np.ndarray, reference_sr: int):
    """Resample reference, estimate integer-sample lag, and return aligned overlap.

    Cross-correlation is estimated on a decimated mono copy, then refined at
    full rate around the coarse lag. The returned arrays have equal dimensions.
    """
    if target.ndim != 2 or reference.ndim != 2:
        raise ValueError("audio arrays must be two-dimensional (frames, channels)")
    if len(target) == 0 or len(reference) == 0:
        raise ValueError("target/reference audio must not be empty")
    if target_sr <= 0 or reference_sr <= 0:
        raise ValueError("sample rates must be positive")

    resample_info = None
    if reference_sr != target_sr:
        ratio = Fraction(target_sr, reference_sr).limit_denominator(100000)
        reference = resample_poly(reference, ratio.numerator, ratio.denominator, axis=0)
        resample_info = {
            "from_hz": int(reference_sr), "to_hz": int(target_sr),
            "up": int(ratio.numerator), "down": int(ratio.denominator),
        }

    target_cmp, reference_cmp, channel_mode = _to_mono_or_match_channels(target, reference)
    t = target_cmp.mean(axis=1).astype(np.float64)
    r = reference_cmp.mean(axis=1).astype(np.float64)

    # Decimation provides a cheap coarse alignment while suppressing the 8 kHz
    # ASK carrier through the anti-alias filter in resample_poly.
    factor = max(1, int(round(target_sr / 4000)))
    td = resample_poly(t, 1, factor)
    rd = resample_poly(r, 1, factor)
    td = td - td.mean()
    rd = rd - rd.mean()
    corr = correlate(td, rd, mode="full", method="fft")
    lags = correlation_lags(len(td), len(rd), mode="full")
    coarse_lag = int(lags[int(np.argmax(np.abs(corr)))]) * factor

    # Refine at original sample rate in the small neighborhood left by decimation.
    candidates = range(coarse_lag - factor, coarse_lag + factor + 1)
    best_lag, best_score = coarse_lag, -1.0
    for lag in candidates:
        try:
            ts, rs, _, _ = _slice_for_lag(target_cmp, reference_cmp, lag)
        except ValueError:
            continue
        x = ts.mean(axis=1).astype(np.float64)
        y = rs.mean(axis=1).astype(np.float64)
        x -= x.mean()
        y -= y.mean()
        denom = float(np.linalg.norm(x) * np.linalg.norm(y))
        score = abs(float(np.dot(x, y)) / denom) if denom else 0.0
        if score > best_score:
            best_lag, best_score = lag, score

    ta, ra, target_start, reference_start = _slice_for_lag(target_cmp, reference_cmp, best_lag)
    if ta.shape != ra.shape:
        raise RuntimeError("internal alignment error: overlap shapes differ")
    metadata = {
        "target_sample_rate_hz": int(target_sr),
        "reference_sample_rate_hz_original": int(reference_sr),
        "reference_resampling": resample_info,
        "alignment_lag_samples": int(best_lag),
        "alignment_lag_seconds": float(best_lag / target_sr),
        "target_start_sample": int(target_start),
        "reference_start_sample": int(reference_start),
        "overlap_frames": int(len(ta)),
        "overlap_duration_seconds": float(len(ta) / target_sr),
        "normalized_abs_correlation": float(best_score),
        "channel_handling": channel_mode,
        "truncated_to_overlap": bool(len(ta) != len(target) or len(ra) != len(reference)),
    }
    return ta, ra, metadata
