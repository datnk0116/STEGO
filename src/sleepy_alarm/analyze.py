#!/usr/bin/env python3
"""Non-destructive metadata, waveform and STFT inspection for audio challenges."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import stft
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
    freqs, times, z = stft(mono, fs=sr, nperseg=min(args.nperseg, frames),
                            noverlap=min(args.noverlap, max(0, min(args.nperseg, frames)-1)))
    magnitude = np.abs(z)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    waveform_path = args.out_dir / "waveform.png"
    spec_path = args.out_dir / "spectrogram.png"
    t = np.arange(frames) / sr
    plt.figure(figsize=(12, 3))
    plt.plot(t, mono, linewidth=0.5)
    plt.xlabel("Time (s)"); plt.ylabel("Amplitude"); plt.title("Mono waveform")
    plt.tight_layout(); plt.savefig(waveform_path, dpi=160); plt.close()
    plt.figure(figsize=(12, 4))
    plt.pcolormesh(times, freqs, 20*np.log10(np.maximum(magnitude, 1e-12)),
                   shading="auto")
    plt.ylim(0, sr/2); plt.xlabel("Time (s)"); plt.ylabel("Frequency (Hz)")
    plt.title(f"STFT magnitude (nperseg={min(args.nperseg, frames)}, noverlap={min(args.noverlap, max(0, min(args.nperseg, frames)-1))})")
    plt.colorbar(label="Magnitude (dB)"); plt.tight_layout()
    plt.savefig(spec_path, dpi=160); plt.close()
    result = {
        "file": str(args.audio), "sha256": sha256(args.audio),
        "format": sf.info(args.audio).format, "subtype": sf.info(args.audio).subtype,
        "samplerate_hz": int(sr), "channels": int(channels), "frames": int(frames),
        "duration_seconds": float(duration),
        "peak_amplitude": float(np.max(np.abs(audio))),
        "rms_amplitude": float(np.sqrt(np.mean(audio**2))),
        "clipped_sample_fraction": float(np.mean(np.abs(audio) >= 0.999)),
        "stft": {"nperseg": int(min(args.nperseg, frames)),
                 "noverlap": int(min(args.noverlap, max(0, min(args.nperseg, frames)-1))),
                 "frequency_bins": int(len(freqs)), "time_frames": int(len(times))},
        "plots": [str(waveform_path), str(spec_path)],
        "note": "Plots are exploratory evidence, not proof of steganography by themselves."
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
