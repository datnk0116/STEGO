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
- `src/experiments/`: Blue 3, paired audio and asymmetric target/reference robustness experiments.
- `tests/`: synthetic regression tests; these complement, not replace, artifact tests.
- `results/`: machine-readable outputs, plots, CSVs and execution logs.
- `report/REPORT.md`: report aligned to the UET.CN3124 assignment rubric.
- `references/REFERENCES.md`: cited primary sources and technical documentation.
- `docs/DEFENSE_QA.md`: technical questions for explaining the implementation, evidence and limits if verification is requested.
- `docs/PERSONAL_REFLECTION_TEMPLATE.md`: prompts for the student's own reflection; never invent personal experience or hours.
- `docs/QUALITY_GATE.md`: local artifact/test verification procedure.
- `docs/QUALITY_ASSURANCE_PLAN.md`: quality-assurance plan, acceptance criteria and evidence index.

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

The official MATLAB generator specifies a 8 kHz carrier, 50 baud, 0.02 s per symbol and a 7-second ASK transmission on the first/left channel. The optional reference file is resampled and aligned by cross-correlation. The decoder preserves the leading distributed-stream prefix that does not overlap the reference, then appends the aligned residual; this prevents losing the first ASK symbols when the original/distributed MP3 streams have different encoder priming offsets.

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

Additional one-sided robustness experiment (transforms target and reference separately):

```bash
python src/experiments/sleepy_alarm_asymmetric_robustness.py \
  data/sleepy_alarm/morning_n_breakfast.mp3 \
  --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 \
  --expected 'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'
```

This writes `asymmetric_robustness.json` and `asymmetric_robustness.csv` under `results/sleepy_alarm/asymmetric_robustness/`. The committed run records 3/6 one-sided variants as PASS: both one-sided resampling round-trips pass, while target-only and reference-only gain changes (0.5× and 1.5×) fail exact decoding. The detailed JSON/CSV are the source of truth; rerun the command after changing the decoder or input artifacts.

The expected flag is taken from the official creator bitmap solely for exact validation. The decoder must reconstruct the text from the distributed MP3; it must not read the expected text as its extraction input. A structural-only run without `--expected` reports `success: null` and `format_valid` separately.

## Build the submission locally (no GitHub Actions run required)

Install the document tools once (`pandoc`, LibreOffice Writer and `poppler-utils`), then run:

```bash
python scripts/build_submission.py
```

Outputs are written under `results/submission/`: the DOCX, PDF and `STUDENT_UETCN3124_Scripts.zip`. The build stops if the main body exceeds 15 pages. The report remains a Markdown source of truth; binary submission files must be regenerated after report changes.

## Tests and local quality gate

Run the one-command local evidence gate:

```bash
python scripts/verify_reproducibility.py
```

The gate runs the complete unittest suite, checks SHA-256 and byte sizes for all three official artifacts, verifies the Blue 3 flag and the 39-character Sleepy Alarm exact-match, and records the reference-free result as a limitation measurement. The committed gate evidence records **22/22 tests passed (exit code 0)**, all three artifact hashes passed, and both official decoders matched their expected payloads under the documented conditions. The JSON records revision `a040e3863145038b786ba6719629e636fdf2e565`. Commit `3bb2b57790d164a6997ee1afe157a0fc7a8a8807` subsequently packages the gate log and JSON. Comparing these two revisions shows that the packaging commit changes only `results/logs/quality-gate-tests.log` and `results/verification/quality-gate.json`; it does not change source or test files. `results/logs/unit-tests.log` remains a historical six-test log; use `results/logs/quality-gate-tests.log` as the current 22-test evidence.

The GitHub Actions workflow is optional. The quality gate does not start GitHub Actions or build DOCX/PDF/ZIP. For those local submission artifacts, the separate command is `python scripts/build_submission.py`.


### Steganalysis triage and expanded experiments

The first-pass detector is intentionally explainable and challenge-oriented; it is **not** a universal or calibrated classifier. It extracts modal RGB concentration/channel dispersion for images and 8 kHz band-energy ratio/50-baud block-RMS variation for audio. Thresholds are fixed heuristics in `src/steganalysis.py`.

```bash
python -m unittest discover -s tests -v
python src/experiments/steganalysis_benchmark.py
python src/experiments/blue3_extended_robustness.py data/blue3/blue.png
python src/experiments/sleepy_alarm_robustness_matrix.py \
  data/sleepy_alarm/morning_n_breakfast.mp3 \
  --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 \
  --expected 'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'
```

The benchmark includes deterministic **synthetic benign controls** (seed 20261114) and one official positive artifact per modality. Its precision/recall/F1/FPR are descriptive of this small constructed set only; they are not estimates of real-world detection performance. The benchmark also compares reference-free and reference-assisted Sleepy Alarm extraction. The committed comparison is complete: reference-free extraction fails exact decoding (26 characters, 49 separators), while reference-assisted extraction succeeds. Do not describe the reference-free mode as successful.

The expanded Blue 3 matrix tests brightness, contrast, blur, crop and seeded Gaussian noise. Its committed output includes candidate-at-baseline-length, position accuracy, Levenshtein edit distance and normalized edit similarity: 1/9 variants exact-match; brightness 0.9 still recovers 47/50 positions (edit distance 3), brightness 1.1 recovers 28/50 (edit distance 20), and two Gaussian-noise levels produce no candidate at the baseline length. The audio matrix covers one-sided gain, AWGN at several SNRs, band-pass filtering and resampling round-trip; its 23 trials include BER, symbol error rate and separator precision/recall. It records 7/23 exact matches, mean trial SER 12.31%, mean trial BER 12.97%, mean separator precision 77.07% and recall 93.14% (arithmetic means including baseline). The detector benchmark reports image TP=5/TN=12/FP=0/FN=0 on its constructed set, but audio TP=0/TN=8/FP=0/FN=5 (recall=0). Positive samples are derivatives of one official artifact per modality and benign controls are synthetic; these metrics are not real-world performance estimates. The reference-free Sleepy Alarm trial also fails (26 characters, 49 separators); do not call it blind decoding.

## Evidence conventions

Each result must include the source artifact, SHA-256, command, parameters, outputs and runtime where measured. Original files under `data/` are immutable. Transformed variants are written under `results/`; they must never overwrite source artifacts.

## Scope

All analysis is offline and limited to the two public challenge artifacts. No external target is scanned, exploited or contacted.

## Critical evaluation and limitations

The report includes a dedicated critical-evaluation section covering the threat model, construct/internal/external validity, decoder assumptions, detector failure analysis, asymmetric robustness, and prioritized future experiments. Important limitations are intentionally retained rather than hidden:

- Sleepy Alarm is currently reference-assisted; the saved reference-free comparison fails exact decoding.
- The audio heuristic detector has recall=0 on the current small benchmark (TP=0, FN=5).
- The image detector's perfect score is challenge-family-specific and based on synthetic controls plus derivatives of one source artifact.
- Blue 3 extended robustness passes 1/9 variants; Sleepy Alarm's one-sided robustness passes 3/6 variants.
- The old `unit-tests.log` covers six tests only. Current committed evidence is the separate quality-gate log with 22/22 tests passed on the recorded source commit; rerun it after any source/test change.

See `report/REPORT.md` section 11.7–11.9, `docs/DEFENSE_QA.md`, and `docs/QUALITY_GATE.md` for the threat model, validity discussion, defense questions, and reproducible verification procedure. These findings describe the committed experiments only and are not claims about all steganography methods.

