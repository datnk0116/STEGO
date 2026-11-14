# Steganography CTF Study — UET.CN3124

A reproducible study of two public CTF challenges in one academic topic:

1. **Blue 3 (BYUCTF)** — image-domain pixel-difference steganography.
2. **Sleepy Alarm (ImaginaryCTF 2024)** — audio-domain ASK steganography.

## Evidence and verification policy

This repository distinguishes three kinds of evidence:

- **Official-source facts:** challenge descriptions, creator source and official challenge artifacts.
- **Locally reproduced results:** outputs accompanied by command logs, input hashes and generated files under `results/`.
- **Pending work:** explicitly marked items without a successful run on the official artifact.

A passing synthetic unit test does not prove that the official challenge artifact has been solved. Sleepy Alarm is considered solved only when the decoded 39-character text exactly matches the expected value extracted independently from the official `createsignal.m` bitmap.

## Repository structure

- `data/`: the three official challenge artifacts and provenance notes.
- `src/solve_challenges.py`: Blue 3 and Sleepy Alarm decoders.
- `src/audio_alignment.py`: reference resampling and time alignment.
- `src/blue3/`: image inspection and visualization.
- `src/sleepy_alarm/`: waveform, spectrogram and ASK-envelope analysis.
- `src/experiments/`: Blue 3 and audio robustness experiments.
- `tests/`: synthetic regression tests; these complement, not replace, artifact tests.
- `results/`: machine-readable outputs, plots, CSVs and execution logs.
- `report/REPORT.md`: report aligned to the UET.CN3124 assignment rubric.
- `references/REFERENCES.md`: cited primary sources and technical documentation.

## Environment setup

Python 3.14 is the recorded environment. Use uv:

```bash
uv python install 3.14
uv venv --python 3.14
source .venv/bin/activate
uv pip install -r requirements.txt
python scripts/check_environment.py
```

## Run the complete local workflow

The challenge artifacts are already committed to `data/`. The downloader verifies official byte sizes and skips existing files:

```bash
python scripts/download_artifacts.py all
python -m unittest discover -s tests -v
```

### Blue 3

```bash
python src/blue3/analyze.py data/blue3/blue.png \
  --output results/blue3/analysis.json

python src/solve_challenges.py blue3 data/blue3/blue.png

python src/blue3/visualize.py data/blue3/blue.png \
  --length 50 --out-dir results/blue3/figures

python src/experiments/blue3_robustness.py data/blue3/blue.png
```

### Sleepy Alarm

The official MATLAB generator specifies a 8 kHz carrier, 50 baud, 0.02 s per symbol and a 7-second ASK transmission on the first/left channel. The optional reference file is resampled and aligned by cross-correlation; the unaligned MP3 encoder-delay prefix is discarded.

```bash
python src/sleepy_alarm/analyze.py \
  data/sleepy_alarm/morning_n_breakfast.mp3 \
  --reference data/sleepy_alarm/morning_n_breakfast_original.mp3

python src/solve_challenges.py sleepy-alarm \
  data/sleepy_alarm/morning_n_breakfast.mp3 \
  --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 \
  --expected 'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'

python src/experiments/sleepy_alarm_robustness.py \
  data/sleepy_alarm/morning_n_breakfast.mp3 \
  --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 \
  --expected 'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'
```

The expected flag is taken from the official creator bitmap solely for exact validation. The decoder must reconstruct the text from the distributed MP3; it must not read the expected text as its extraction input. A structural-only run without `--expected` reports `success: null` and `format_valid` separately.

## Tests and continuous integration

```bash
python -m unittest discover -s tests -v
```

The GitHub Actions workflow runs synthetic tests and the two official challenge workflows on pushes to `main`. It stores logs, JSON, visualizations and experiment CSVs as repository evidence. An official Sleepy Alarm run is marked successful only when exact ground-truth comparison passes.

## Evidence conventions

Each result must include the source artifact, SHA-256, command, parameters, outputs and runtime where measured. Original files under `data/` are immutable. Transformed variants are written under `results/`; they must never overwrite source artifacts.

## Scope

All analysis is offline and limited to the two public challenge artifacts. No external target is scanned, exploited or contacted.
