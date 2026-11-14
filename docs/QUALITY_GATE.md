# Quality gate and reproducible evidence

This procedure validates the pinned official challenge artifacts, runs the complete
unit/integration suite, and verifies both official payloads. It does not invoke
GitHub Actions and does not build DOCX/PDF/ZIP.

## One-command local verification

From the repository root with the project virtual environment active:

```bash
python scripts/verify_reproducibility.py
```

The command:

1. Runs `python -m unittest discover -s tests -v`.
2. Verifies byte sizes and SHA-256 of all three pinned official artifacts.
3. Runs the Blue 3 decoder against the official PNG.
4. Runs Sleepy Alarm with the official reference and validates all 39 bytes.
5. Records the current reference-free result as a limitation measurement; this does
   not fail the gate by itself.
6. Captures the Git commit, branch, working-tree status, Python/package versions,
   test output and challenge verification details.

Outputs:

- `results/logs/quality-gate-tests.log`
- `results/verification/quality-gate.json`

The gate exits with code 0 only when all tests pass, all three hashes match,
and both reference-assisted official challenge decoders produce exact matches.

## Robustness experiments and partial-recovery metrics

Run these separately after the quality gate:

```bash
python src/experiments/blue3_extended_robustness.py data/blue3/blue.png

python src/experiments/sleepy_alarm_robustness_matrix.py \
  data/sleepy_alarm/morning_n_breakfast.mp3 \
  --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 \
  --expected 'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'
```

The Blue 3 matrix now records a candidate at the baseline flag length, position
accuracy, Levenshtein edit distance and normalized edit similarity. If there is no
candidate at that length, edit distance is marked unavailable rather than inventing
a zero or treating a missing string as a measured decode.

The audio matrix now records bit error rate (BER), symbol error rate, and separator
precision/recall for every trial. Ground truth is used only after extraction to score
the observed symbol stream; it is never passed into the extraction algorithm except
as the existing exact-match validator.

Historical PASS/FAIL counts (Blue 3 1/9; Sleepy Alarm 7/23) remain valid for their
original experiment outputs. The new partial-recovery metrics are only available after
rerunning the updated scripts; do not retroactively infer these values from old JSON.

## Evidence integrity rules

- Do not overwrite original files in `data/`.
- Keep transformed files and outputs under `results/`.
- Commit the quality-gate JSON and logs only after reviewing them.
- Record the commit SHA that was actually tested.
- A synthetic test pass is not a substitute for the official-artifact integration tests.
- A successful gate verifies this repository revision and these fixed artifacts; it
  does not establish blind decoding or population-level detector performance.
