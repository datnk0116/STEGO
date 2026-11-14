# Results and evidence

<!-- PROVENANCE_STATUS_START -->
**Verification provenance:** The canonical run record is results/verification/provenance.json. tested_commit identifies the source revision actually executed. The evidence-packaging commit and current HEAD are derived from Git history by scripts/check_provenance_consistency.py; they are not copied into this snapshot. Documentation-only changes do not stale the technical gate. Changes to source, tests, challenge data, dependencies, artifact manifest, or gate implementation do. Submission-package freshness is assessed separately.
<!-- PROVENANCE_STATUS_END -->


This directory contains committed technical outputs and experiment evidence. Final DOCX/PDF/ZIP files are generated locally under `results/submission/` and are intentionally excluded from the source ZIP to avoid nesting generated submission artifacts. The logbook template is included as a separate record and must only be filled from actual work.

## Current verification outputs

The previously recorded baseline is a historical verification snapshot. Its tested commit is stored in results/verification/provenance.json; the evidence-packaging commit and current HEAD are derived dynamically from Git history. The baseline did not capture pre-run working-tree state. New provenance checker/tests must be covered by a new full local gate before the evidence is current.

- verification/quality-gate.json: gate result for the run identified by canonical provenance. The prior baseline recorded 22/22 tests, three artifact checks, Blue 3 exact-match and Sleepy Alarm reference-assisted exact-match; do not reuse that count as the result of a newer run.
- logs/quality-gate-tests.log: full 22-test run corresponding to the source commit recorded in the JSON.
- logs/unit-tests.log: historical six-test log from an older revision; retain for historical debugging only and never cite as current full-suite evidence.
- artifact_manifest.json: upstream source, byte size and SHA-256 for each of the three pinned official artifacts.
- environment.json: environment captured by an earlier run. For the environment associated with the latest gate, use the environment object in verification/quality-gate.json.

## Challenge outputs

### Blue 3
- blue3/analysis.json: PNG metadata and RGB statistics.
- blue3/figures/: diagnostics and visualizations.
- blue3/robustness/: JPEG and resize experiments.
- blue3/extended_robustness/extended_robustness.json and CSV: nine brightness, contrast, blur, crop and Gaussian-noise transformations, with exact-match and partial character metrics.

The extended matrix has 1/9 exact-match. Brightness 0.9 still produces a 50-character candidate with 47/50 matching positions and edit distance 3. Brightness 1.1 has 28/50 matching positions and edit distance 20. Two Gaussian-noise cases have no candidate at the baseline length; edit distance is therefore null.

### Sleepy Alarm
- sleepy_alarm/analysis.json: metadata, reference alignment, STFT and ASK measurements.
- sleepy_alarm/solver.json: reference-assisted decoded stream, cluster centers, byte errors and exact-match.
- sleepy_alarm/robustness/: paired target/reference transformations.
- sleepy_alarm/asymmetric_robustness/: one-sided target/reference transformations.
- sleepy_alarm/robustness_matrix/robustness_matrix.json and CSV: 23 one-sided trials, including per-trial BER, symbol error rate and separator precision/recall.

The extended matrix has 7/23 exact-match. Across the 23 trials, the unweighted arithmetic means (including baseline) are symbol error rate 12.31%, bit error rate 12.97%, separator precision 77.07% and separator recall 93.14%. These figures describe only this challenge artifact and the exact tested transformations.

## Steganalysis benchmark

- steganalysis/benchmark.json and CSV: image TP=5/TN=12/FP=0/FN=0; audio TP=0/TN=8/FP=0/FN=5.
- steganalysis/reference_comparison.json: reference-free Sleepy Alarm fails exact decoding (26 characters, 49 separators); reference-assisted mode succeeds.

Positive samples are derived from one official challenge artifact per modality, while benign controls are synthetic. The image score is not evidence of generalization. The audio heuristic detector's recall is zero on this benchmark. Do not hide or tune away these results.

## Interpretation and integrity

Do not label a run successful because a string matches only a flag prefix/suffix. Sleepy Alarm success requires exact-match of the full 39-character ground truth, 350 symbols, 38 separators and no byte errors under the documented reference-assisted setup.

Never invent runtimes, metrics or experimental activity. Each robustness result applies only to the input artifact and parameters recorded in its JSON/CSV. Do not modify the original inputs under data/.

The historical failed attempt is preserved in 2026-11-14/initial-run.md; it must not be confused with the later exact-match solver output.
