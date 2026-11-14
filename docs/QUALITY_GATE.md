# Quality gate and reproducible evidence

<!-- PROVENANCE_STATUS_START -->
**Verification provenance:** The canonical run record is results/verification/provenance.json. tested_commit identifies the source revision actually executed. The evidence-packaging commit and current HEAD are derived from Git history by scripts/check_provenance_consistency.py; they are not copied into this snapshot. Documentation-only changes do not stale the technical gate. Changes to source, tests, challenge data, dependencies, artifact manifest, or gate implementation do. Submission-package freshness is assessed separately.
<!-- PROVENANCE_STATUS_END -->

## Purpose

This local procedure validates the pinned official challenge artifacts, runs the complete discovered unittest suite, verifies both documented official payloads, and checks provenance consistency. It does not invoke GitHub Actions and does not rebuild DOCX/PDF/ZIP.

## Canonical evidence

- results/verification/provenance.json is the canonical run snapshot.
- results/verification/quality-gate.json stores the actual gate result and tested commit.
- results/logs/quality-gate-tests.log stores the test output for that same run.
- results/artifact_manifest.json records upstream source, byte size and SHA-256 for each pinned official challenge artifact.
- The strict checker derives the evidence-packaging commit from Git history by matching the committed Git blobs for the gate JSON and log. It derives current HEAD at check time. Neither value is embedded in the provenance snapshot, avoiding a self-referential commit hash.

The existing 22/22 test result is a historical baseline. Its original run did not capture the pre-run working-tree state, so that fact is explicitly unknown; the old post-generation status field cannot be used to reconstruct it. The canonical migration snapshot preserves this uncertainty. New runs capture the working-tree status before the gate writes any output.

## Local verification

Run from a clean checkout after committing source, tests, data, dependencies and documentation:

~~~bash
python scripts/verify_reproducibility.py
~~~

The gate:
1. Captures HEAD, branch and git status before creating or rewriting output files.
2. Runs python -m unittest discover -s tests -v; expected test count is calculated from checked-in test methods, not hardcoded.
3. Checks byte size and SHA-256 for all pinned official artifacts.
4. Runs Blue 3 and Sleepy Alarm reference-assisted decoding against the official files.
5. Records reference-free Sleepy Alarm as a limitation measurement; its failure does not get relabeled as success.
6. Writes quality-gate JSON, test log and canonical provenance snapshot.
7. Runs the fast provenance checker in --pre-commit mode. The process exits non-zero if either the gate or pre-commit consistency check fails.

Before committing generated gate evidence, the expected working-tree changes are limited to:
- results/logs/quality-gate-tests.log
- results/verification/quality-gate.json
- results/verification/provenance.json

Then commit those outputs and run the strict checker:

~~~bash
git add results/logs/quality-gate-tests.log results/verification/quality-gate.json results/verification/provenance.json
git commit -m "test: record local provenance verification"
python scripts/check_provenance_consistency.py
~~~

## Freshness semantics

The checker distinguishes three classes:

- **Technical gate stale:** changes to src/, tests/, data/, dependencies, artifact manifest, workflow/configuration, or gate implementation after tested_commit. The strict checker fails this state.
- **Documentation-only:** does not invalidate unit/integration evidence, but each of the six documentation status blocks must match the canonical statement.
- **Submission-package stale/unverified:** report or package-input changes require rebuilding DOCX/PDF/ZIP. This is tracked separately; use --require-submission-package when that validation is required.

A synthetic test is not a substitute for official-artifact integration checks. A passing gate verifies only the pinned artifacts and the tested revision; it does not establish blind decoding, robustness on other files, or population-level steganalysis performance.

## Existing experiment outputs

The committed robustness scripts and JSON/CSV outputs are historical experiment evidence. Do not rerun them merely to refresh provenance. Rerun those experiments only when their source, input artifacts, seed or parameters change. Keep original files under data/ immutable and transformed outputs under results/.

## Interpretation reminders

- Blue 3 extended robustness: 9 transformations, 1 exact-match; retain partial-character metrics.
- Sleepy Alarm extended robustness: 23 trials, 7 exact-match; aggregate means are unweighted arithmetic means including baseline, not population estimates.
- Sleepy Alarm reference-free decoding failed in the recorded baseline; do not describe it as blind decoding.
- The audio steganalysis benchmark recall of zero is a measured failure on the constructed set, not a universal claim about audio steganalysis.

## Submission package check

The technical gate does not rebuild submission binaries. After the report and source-package inputs are final, run python scripts/build_submission.py --max-main-pages 15, inspect the generated PDF, and inspect the ZIP contents. The strict provenance checker reports the package as NOT_VERIFIED until an independently verifiable package build record exists.
