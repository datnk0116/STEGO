# Steganography CTF Study — UET.CN3124

<!-- PROVENANCE_STATUS_START -->
**Verification provenance:** The canonical run record is results/verification/provenance.json. tested_commit identifies the source revision actually executed. The evidence-packaging commit and current HEAD are derived from Git history by scripts/check_provenance_consistency.py; they are not copied into this snapshot. Documentation-only changes do not stale the technical gate. Changes to source, tests, challenge data, dependencies, artifact manifest, or gate implementation do. Submission-package freshness is assessed separately.
<!-- PROVENANCE_STATUS_END -->


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

The prioritized remaining work, file-by-file changes and acceptance criteria are tracked in [docs/IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md).

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

Outputs are written under `results/submission/`: the DOCX, PDF and `STUDENT_UETCN3124_Scripts.zip`. The local PDF checker uses a 20-page sanity ceiling for this build. This is a local checking allowance and does not override any stricter page limit stated in the course instructions. The report remains a Markdown source of truth; binary submission files must be regenerated after report changes.

## Tests and local quality gate

Run the one-command local evidence gate:

```bash
python scripts/verify_reproducibility.py
```

Historical committed gate evidence (14 November 2026): **38/38 tests passed** (exit code 0; 5.358 s), all **3/3 official artifact** size/SHA-256 checks passed, and both Blue 3 and reference-assisted Sleepy Alarm exact-matched. The run tested source commit `38fbecab7aea8c241243fb50d044aea90ab657f7`; its evidence-packaging commit is `29c7e9e8e98d96e20e5172a63a359cfefd22edcc`. This is evidence for that historical revision only. The final-improvement branch changes source, tests and gate implementation, so its technical gate is **STALE pending a new local run**; do not present 38/38 as verification of the new branch. The pre-run working tree was captured as clean. The earlier **22/22** result remains a historical baseline and is not overwritten. The canonical JSON/log pair is `results/verification/quality-gate.json` and `results/logs/quality-gate-tests.log`; `results/logs/unit-tests.log` remains a historical six-test log. After documentation-only updates, run the strict provenance checker to verify current HEAD; rerun the full gate only when source, tests, challenge data, dependencies, manifest or gate implementation changes.

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

The benchmark includes deterministic **synthetic benign controls** (seed 20261114) and one official positive artifact per modality. Its precision/recall/F1/FPR are descriptive of this small constructed set only; they are not estimates of real-world detection performance. The benchmark also records carrier-only, block-RMS-only and combined-AND audio ablations over whole-file and first-7-second windows with original thresholds. A Mendeley Spanish-speech steganography dataset is identified as a CC BY 4.0 candidate, but has not been downloaded or included in current metrics. The benchmark also compares reference-free and reference-assisted Sleepy Alarm extraction. A sample-manifest checker and tests for file integrity plus host/secret source leakage are ready for a future verified corpus; the current Mendeley manifest template remains empty. The committed comparison is complete: reference-free extraction fails exact decoding (26 characters, 49 separators), while reference-assisted extraction succeeds. Do not describe the reference-free mode as successful.

The expanded Blue 3 matrix tests brightness, contrast, blur, crop and seeded Gaussian noise. Its committed output includes candidate-at-baseline-length, position accuracy, Levenshtein edit distance and normalized edit similarity: 1/9 variants exact-match; brightness 0.9 still recovers 47/50 positions (edit distance 3), brightness 1.1 recovers 28/50 (edit distance 20), and two Gaussian-noise levels produce no candidate at the baseline length. The audio matrix covers one-sided gain, AWGN at several SNRs, band-pass filtering and resampling round-trip; its 23 trials include BER, symbol error rate and separator precision/recall. It records 7/23 exact matches, mean trial SER 12.31%, mean trial BER 12.97%, mean separator precision 77.07% and recall 93.14% (arithmetic means including baseline). The detector benchmark reports image TP=5/TN=12/FP=0/FN=0 on its constructed set, but audio TP=0/TN=8/FP=0/FN=5 (recall=0). Positive samples are derivatives of one official artifact per modality and benign controls are synthetic; these metrics are not real-world performance estimates. For the five positive audio samples, the recorded carrier-band energy ratio is approximately 0.000204, about 98 times below the fixed 0.02 threshold; block-RMS CV is approximately 0.987 and exceeds its 0.15 threshold. Because the classifier requires both conditions (AND), the carrier-band condition alone rejects every positive in this constructed set. This diagnoses the current benchmark failure; it does not establish the cause for other recordings or justify threshold tuning on this same test set. The reference-free Sleepy Alarm trial also fails (26 characters, 49 separators); do not call it blind decoding.

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
- The old `unit-tests.log` covers six tests only; 22/22 is retained as a historical baseline, while the latest canonical gate records 38/38 on tested commit `38fbecab7aea8c241243fb50d044aea90ab657f7`. Use the matching quality-gate JSON/log pair identified by canonical provenance; rerun the full gate after technical source/test/input changes, not for documentation-only edits.

See `report/REPORT.md` section 11.7–11.9, `docs/DEFENSE_QA.md`, and `docs/QUALITY_GATE.md` for the threat model, validity discussion, defense questions, and reproducible verification procedure. These findings describe the committed experiments only and are not claims about all steganography methods.



### External audio corpus integrity (only after actual collection)

The Mendeley record is currently **identified but not downloaded**. Do not treat the empty `results/steganalysis/external_dataset_manifest.template.json` as a dataset. After obtaining and hashing real samples, populate a manifest with per-file source, license, label, carrier, transformation, host/secret IDs, split, byte size and SHA-256, then run:

```bash
python scripts/check_steganalysis_dataset_manifest.py results/steganalysis/external_dataset_manifest.json
```

The checker rejects missing or hash-mismatched files, repeated files across splits, and host/secret source IDs crossing train/validation/test. Its unit tests use temporary fixtures only; they do not claim a benchmark on the external corpus.

### Blue 3 upstream comparison

BYUCTF reference source is pinned at commit `18c8f246756e79069c1cb1753c8bfea5e73e31f5`. Run:

```bash
python src/blue3/reference_comparison.py data/blue3/blue.png
```

The script writes `results/blue3/reference_comparison/comparison.json` and `.log`; it compares candidate output and length, not speed. The committed source review is marked NOT_RUN until this command is executed on the official artifact.

### Submission package manifest

After final source/report changes, build with `python scripts/build_submission.py --max-main-pages 20`, visually inspect the PDF, and follow `results/submission/README.md`. A package is not VERIFIED until manifest, hashes, PDF checks and ZIP integrity pass.
