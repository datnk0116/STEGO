# Steganography CTF Study — UET.CN3124

A reproducible study of image and audio steganography using two public CTF challenges:

1. **Blue 3 (BYUCTF)** — image/pixel-difference steganography.
2. **Sleepy Alarm (ImaginaryCTF 2024)** — audio signal analysis.

## Academic integrity and evidence status

This repository is a research workspace and reproducibility package. Do not treat an upstream write-up as personal experimental work. Run the supplied scripts, preserve your own terminal output/screenshots, and replace all `[TO BE RECORDED]` fields in the report with measured results before submission.

No flag, runtime, metric, or successful experiment is claimed unless it is produced locally and recorded in `results/`.

## Structure

- `report/REPORT.md`: report aligned with UET.CN3124 rubric.
- `src/blue3/`: image inspection and pixel-difference analysis.
- `src/sleepy_alarm/`: audio inspection and frequency-domain analysis.
- `scripts/`: deterministic setup and integrity checks.
- `data/README.md`: upstream artifact acquisition instructions.
- `results/README.md`: evidence and experiment record template.
- `references/REFERENCES.md`: primary sources and citation notes.

## Quick start

Requirements: Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/check_environment.py
```

Download the pinned official artifacts (byte-size checked) with `python scripts/download_artifacts.py all`. Then run:

```bash
python src/blue3/analyze.py data/blue3/blue.png
python src/solve_challenges.py blue3 data/blue3/blue.png
python src/sleepy_alarm/analyze.py data/sleepy_alarm/morning_n_breakfast.mp3
python src/solve_challenges.py sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3
```

The audio filename is intentionally not hard-coded; use the exact artifact filename from the official challenge repository.

## Reproducibility

Record OS, Python version, dependency versions, input SHA-256, commands, outputs, elapsed time, and screenshots. Keep original challenge files immutable. Generated files belong in `results/`.

## Scope

The work is limited to offline analysis of challenge-provided files. It does not scan, exploit, or collect data from third-party systems.

## Status

Analysis scripts and independent solver logic are committed. Download and run the official artifacts locally; record generated evidence before making final experimental claims.
