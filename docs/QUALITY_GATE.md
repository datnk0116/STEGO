# Quality gate and reproducible evidence

This procedure validates the pinned official challenge artifacts, runs the full test suite, and verifies both official payloads. It does not invoke GitHub Actions and does not build DOCX/PDF/ZIP.

## Latest committed verification

The committed gate evidence records:
- **22/22 unittest methods passed**, exit code 0.
- All three pinned artifact byte-size and SHA-256 checks passed.
- Blue 3 decoded the official flag exactly.
- Sleepy Alarm decoded the full 39-character payload exactly with the supplied reference: 350 symbols, 38 separators, 39 bytes and no byte errors.
- Reference-free Sleepy Alarm was measured separately and failed exact decoding (26 characters, 49 separators); that limitation does not fail the quality gate.

The quality-gate JSON identifies the source revision tested: 11cd5e3216e779b6101b22cd891689ecdf9b8e54. Commit 3015d5ddcab12fb99d53158c4029750d7b8805b3 subsequently committed the generated logs and current robustness JSON/CSV. That evidence-packaging commit did not change source or test files. This distinction matters: a run records the source commit before its own output files are committed, so the JSON's tested commit is not expected to be the later commit that stores the JSON.

Files:
- results/logs/quality-gate-tests.log
- results/verification/quality-gate.json

The older results/logs/unit-tests.log contains six tests from a previous revision. It is historical evidence only; do not cite it as the current full-suite result.

## Re-run locally after source, test or artifact changes

From the repository root, with the project environment active:

~~~bash
python scripts/verify_reproducibility.py
~~~

The command:
1. Runs python -m unittest discover -s tests -v.
2. Verifies byte sizes and SHA-256 of the three pinned official artifacts.
3. Runs the Blue 3 decoder against the official PNG.
4. Runs Sleepy Alarm with the official reference and validates all 39 bytes.
5. Records the reference-free result as a limitation measurement; this does not fail the gate by itself.
6. Captures the tested Git commit, branch, working-tree status, OS, Python/package versions, test output and decoder details.

The gate exits 0 only when all 22 discovered test methods pass, all three artifact checks pass, and both documented official decoder checks exact-match. A passing gate does not establish blind decoding, robustness on other files, or population-level steganalysis performance.

## Committed robustness experiments

The updated scripts have already been run and their JSON/CSV results are committed. Do not mark these outputs pending.

~~~bash
python src/experiments/blue3_extended_robustness.py data/blue3/blue.png

python src/experiments/sleepy_alarm_robustness_matrix.py \
  data/sleepy_alarm/morning_n_breakfast.mp3 \
  --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 \
  --expected 'ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}'
~~~

Run them again only after changing source, input artifacts, seed or parameters. Current committed results:
- Blue 3: 9 transformations, 1 exact-match; partial character metrics included in every row.
- Sleepy Alarm: 23 trials, 7 exact-match; BER, symbol error rate and separator precision/recall are recorded per trial.

### Metric interpretation

Blue 3:
- Position accuracy compares matching character positions at the baseline flag length.
- Levenshtein edit distance counts minimum insertions, deletions and substitutions.
- Normalized edit similarity is 1 - edit_distance / max(expected_length, observed_length, 1).
- If no candidate exists at the baseline length, edit distance is null; it is not a measured zero.

Sleepy Alarm:
- BER is bit errors divided by 312 expected payload bits.
- Symbol error rate compares all 350 positions, including separator positions.
- Separator precision and recall separately count false-positive and false-negative separators.
- Aggregate metrics in the committed JSON are arithmetic means across 23 trials, including baseline. They are not pooled estimates over a population.

The expected text is used only after extraction to score measured symbols and for the exact-match validator; it is not used by the decoder to construct the payload.

## Evidence integrity rules

- Do not overwrite original files in data/.
- Keep transformed files and generated outputs under results/.
- Record the source commit actually tested in the quality-gate JSON.
- A synthetic unit test is not a substitute for official-artifact integration tests.
- Do not tune detector thresholds on the same test data used to report final metrics.
- A successful gate verifies this revision and these fixed artifacts; it does not establish blind decoding or general steganalysis.
