#!/usr/bin/env python3
"""Non-destructive metadata, waveform and STFT inspection for audio challenges."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import stft, butter, sosfiltfilt, hilbert
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audio_alignment import align_reference
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("audio", type=Path)
    p.add_argument("--out-dir", type=Path, default=Path("results/sleepy_alarm"))
    p.add_argument("--nperseg", type=int, default=2048)
    p.add_argument("--noverlap", type=int, default=1536)
    p.add_argument("--carrier", type=float, default=8000.0)
    p.add_argument("--reference", type=Path, help="Optional original/reference audio for aligned difference inspection")
    args = p.parse_args()
    if not args.audio.is_file():
        p.error(f"audio file does not exist: {args.audio}")
    if args.nperseg < 16 or not 0 <= args.noverlap < args.nperseg:
        p.error("require nperseg >= 16 and 0 <= noverlap < nperseg")
    audio, sr = sf.read(args.audio, always_2d=True, dtype="float64")
    if audio.size == 0 or not np.isfinite(audio).all():
        p.error("audio is empty or contains non-finite samples")
    frames, channels = audio.shape
    duration = frames / sr
    mono = audio.mean(axis=1)
    if not 0 < args.carrier < sr / 2:
        p.error("carrier must be below Nyquist")
    low, high = args.carrier - 500, args.carrier + 500
    if low <= 0 or high >= sr / 2:
        p.error("sample rate too low for carrier band")

    reference_info = None
    reference_plot = None
    analysis_signal = audio
    if args.reference:
        ref, ref_sr = sf.read(args.reference, always_2d=True, dtype="float64")
        try:
            aligned_target, aligned_ref, alignment_info = align_reference(
                audio, int(sr), ref, int(ref_sr)
            )
        except ValueError as exc:
            p.error(str(exc))
        residual = aligned_target - aligned_ref
        target_start = int(alignment_info["target_start_sample"])
        if alignment_info["channel_handling"] == "downmixed_to_mono":
            raw_prefix = audio.mean(axis=1, keepdims=True)
        else:
            raw_prefix = audio
        prefix = raw_prefix[:target_start] if target_start > 0 else raw_prefix[:0]
        # Preserve the leading distributed-track samples excluded from the
        # reference overlap so the ASK payload still starts at time zero.
        analysis_signal = np.concatenate((prefix, residual), axis=0)
        reference_info = {
            "file": str(args.reference),
            "sha256": sha256(args.reference),
            **alignment_info,
            "preserved_prefix_samples": int(len(prefix)),
            "difference_rms": float(np.sqrt(np.mean(residual**2))),
            "difference_peak": float(np.max(np.abs(residual))),
        }
    # The official MATLAB generator adds the ASK waveform to the first audio
    # channel only. Analyze that channel; averaging stereo halves the payload.
    analysis_channel = 0
    analysis_mono = analysis_signal[:, analysis_channel]
    # The full target timeline is restored by prefix preservation above.
    symbol_phase = 0
    transmission_samples = int(round(7.0 * sr))
    end_sample = min(len(analysis_mono), symbol_phase + transmission_samples)
    analysis_mono = analysis_mono[symbol_phase:end_sample]
    analysis_frames = len(analysis_mono)
    if analysis_frames < int(7.0 * sr * 0.95):
        p.error("not enough aligned samples for the 7-second ASK transmission")
    freqs, times, z = stft(analysis_mono, fs=sr, nperseg=min(args.nperseg, analysis_frames),
                            noverlap=min(args.noverlap, max(0, min(args.nperseg, analysis_frames)-1)))
    magnitude = np.abs(z)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    waveform_path = args.out_dir / "waveform.png"
    spec_path = args.out_dir / "spectrogram.png"
    t = np.arange(analysis_frames) / sr
    plt.figure(figsize=(12, 3))
    plt.plot(t, analysis_mono, linewidth=0.5)
    plt.xlabel("Time (s)"); plt.ylabel("Amplitude")
    plt.title("Aligned residual waveform" if args.reference else "Mono waveform")
    plt.tight_layout(); plt.savefig(waveform_path, dpi=160); plt.close()
    plt.figure(figsize=(12, 4))
    plt.pcolormesh(times, freqs, 20*np.log10(np.maximum(magnitude, 1e-12)),
                   shading="auto")
    plt.ylim(0, sr/2); plt.xlabel("Time (s)"); plt.ylabel("Frequency (Hz)")
    plt.title(f"STFT magnitude (nperseg={min(args.nperseg, analysis_frames)}, noverlap={min(args.noverlap, max(0, min(args.nperseg, analysis_frames)-1))})")
    plt.colorbar(label="Magnitude (dB)"); plt.tight_layout()
    plt.savefig(spec_path, dpi=160); plt.close()
    if args.reference:
        r_sos = butter(4, [low, high], btype="bandpass", fs=sr, output="sos")
        residual_band = sosfiltfilt(r_sos, analysis_mono)
        residual_env = np.abs(hilbert(residual_band))
        reference_info["carrier_envelope_median"] = float(np.median(residual_env))
        reference_info["carrier_envelope_p99"] = float(np.percentile(residual_env, 99))
        difference_path = args.out_dir / "reference_difference.png"
        plt.figure(figsize=(12, 3))
        plt.plot(np.arange(len(analysis_mono))/sr, analysis_mono, linewidth=0.5)
        plt.xlabel("Time (s)"); plt.ylabel("Amplitude")
        plt.title("Aligned distributed audio minus original reference")
        plt.tight_layout(); plt.savefig(difference_path, dpi=160); plt.close()
        reference_plot = str(difference_path)
    # Isolate the ASK carrier and inspect its envelope. This complements the
    # spectrogram and makes the 50-baud amplitude states measurable.
    sos = butter(4, [low, high], btype="bandpass", fs=sr, output="sos")
    carrier = sosfiltfilt(sos, analysis_mono)
    envelope = np.abs(hilbert(carrier))
    symbol_samples = sr / 50.0
    symbol_levels = []
    for i in range(int(len(envelope) / symbol_samples)):
        start = int(i * symbol_samples + symbol_samples * 0.25)
        end = int((i + 1) * symbol_samples - symbol_samples * 0.25)
        if end > start:
            symbol_levels.append(float(np.median(envelope[start:end])))
    envelope_path = args.out_dir / "ask_envelope.png"
    plt.figure(figsize=(12, 3))
    plt.plot(np.arange(len(envelope)) / sr, envelope, linewidth=0.5)
    plt.xlabel("Time (s)"); plt.ylabel("Envelope"); plt.title("8 kHz carrier envelope")
    plt.tight_layout(); plt.savefig(envelope_path, dpi=160); plt.close()
    result = {
        "file": str(args.audio),
        "analysis_channel": analysis_channel,
        "symbol_clock_phase_samples_after_alignment": symbol_phase,
        "reference_prefix_samples_preserved": (
            int(reference_info["preserved_prefix_samples"]) if reference_info else 0
        ),
        "expected_ask_symbols": 350, "sha256": sha256(args.audio),
        "format": sf.info(args.audio).format, "subtype": sf.info(args.audio).subtype,
        "samplerate_hz": int(sr), "channels": int(channels), "frames": int(frames),
        "duration_seconds": float(duration),
        "analysis_frames": int(analysis_frames),
        "analysis_duration_seconds": float(analysis_frames/sr),
        "peak_amplitude": float(np.max(np.abs(audio))),
        "rms_amplitude": float(np.sqrt(np.mean(audio**2))),
        "clipped_sample_fraction": float(np.mean(np.abs(audio) >= 0.999)),
        "stft": {"nperseg": int(min(args.nperseg, analysis_frames)),
                 "noverlap": int(min(args.noverlap, max(0, min(args.nperseg, analysis_frames)-1))),
                 "frequency_bins": int(len(freqs)), "time_frames": int(len(times))},
        "reference_comparison": reference_info,
        "ask": {"carrier_hz": args.carrier, "baud": 50, "symbol_duration_seconds": 0.02, "transmission_seconds": 7.0, "envelope_symbol_median_min": min(symbol_levels) if symbol_levels else None, "envelope_symbol_median_max": max(symbol_levels) if symbol_levels else None, "envelope_symbol_count": len(symbol_levels)},
        "plots": [str(waveform_path), str(spec_path), str(envelope_path)] + ([reference_plot] if reference_plot else []),
        "note": "Plots are exploratory evidence, not proof of steganography by themselves."
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
