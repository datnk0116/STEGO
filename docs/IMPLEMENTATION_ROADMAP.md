# STEGO — Implementation Roadmap toward the UET.CN3124 Excellent Rubric

**Repository:** datnk0116/STEGO  
**Scope:** technical repository audit; administrative identity fields, DOCX/PDF/ZIP binaries and personal logbook are not used to award technical points, but remain submission obligations.  
**Policy:** never fabricate results, runtimes, personal reflection, corpus size or experiment history. Do not run GitHub Actions. Do not rerun existing robustness matrices merely to refresh provenance.

## Current implementation status

| Item | Status | Evidence / remaining action |
|---|---|---|
| Canonical provenance migration | Implemented retrospectively | `results/verification/provenance.json`; historical pre-run working-tree state is explicitly unknown |
| Six documentation status blocks | Updated | README, report, quality gate, QA plan, defense Q&A and results README |
| Git-history provenance checker | Implemented | `scripts/check_provenance_consistency.py`; strict and pre-commit modes |
| Provenance regression suite | Implemented | `tests/test_provenance_consistency.py`; validate positive/negative Git-history cases |
| Quality gate integration | Implemented in code | `scripts/verify_reproducibility.py` captures pre-run state, emits provenance and calls pre-commit checker |
| Full gate for the new implementation | **Completed — evidence committed** | `results/verification/quality-gate.json` and matching log: 38/38 tests, exit 0, 5.358 s; 3/3 artifacts; both documented decoders exact-match; tested commit `38fbecab7aea8c241243fb50d044aea90ab657f7` |
| Evidence snapshot | **Committed** | Evidence JSON/log/provenance stored at `29c7e9e8e98d96e20e5172a63a359cfefd22edcc`; historical 22/22 baseline retained separately |
| Strict checker on final docs checkout | **Needs local confirmation** | Documentation-only changes should preserve technical freshness; run `python scripts/check_provenance_consistency.py` after pulling this documentation commit |
| New detector/decoder research | Not started in this revision | Do not present proposed experiments as completed results |
| Submission-package inspection | Not verified | Rebuild and inspect binaries after report/package inputs are finalized |

## P0 — Close the provenance and reproducibility loop

### P0.1 — Run the new local quality gate

**Files:** `scripts/verify_reproducibility.py`, `results/verification/quality-gate.json`, `results/logs/quality-gate-tests.log`, `results/verification/provenance.json`

Steps:
1. For a new technical revision, pull the latest `main` and verify the working tree is clean.
2. Run `python scripts/verify_reproducibility.py` only when source/tests/data/dependencies/manifest/gate implementation changed; the current 38/38 run is already committed.
3. Confirm the script records HEAD and pre-run status before rewriting its own log/JSON.
4. Confirm all discovered unit/integration/provenance test methods ran and passed; do not hardcode the expected count as 22.
5. Confirm three official artifact size/SHA-256 checks.
6. Confirm Blue 3 exact-match and Sleepy Alarm reference-assisted exact-match.
7. Preserve Sleepy Alarm reference-free failure as a limitation; it is not a gate pass condition.
8. Confirm `provenance_precommit_passed=true`.

Acceptance:
- Exit code 0.
- Test count in JSON equals discovered test methods and log count.
- All three artifact hashes match.
- Both documented official decoder checks pass under their stated conditions.
- Pre-commit provenance checker passes.
- Only the three generated evidence files are uncommitted: quality-gate JSON, test log and provenance JSON.

### P0.2 — Commit the evidence as one snapshot

**Files:** the three outputs above.

Steps:
1. Inspect `git diff` and verify that no source/data/experiment outputs were changed by the gate.
2. Commit all three evidence files together.
3. Run `python scripts/check_provenance_consistency.py` in strict mode.
4. Read the derived tested commit, evidence commit and current HEAD from checker output.

Acceptance:
- Evidence commit is inferred from Git blob history, not hardcoded in provenance.
- Provenance blob belongs to the same committed evidence snapshot for a generated run.
- Technical gate freshness is FRESH.
- Working tree has no relevant uncommitted files.
- No GitHub Actions run is required.

### P0.3 — Verify stale/freshness classification

**File:** `scripts/check_provenance_consistency.py`

Required behavior:
- A change in `src/`, `tests/`, `data/`, dependency/configuration files, manifest or gate implementation makes technical evidence STALE.
- Documentation-only changes do not invalidate unit/integration evidence, but the six canonical status blocks must remain synchronized.
- Changes to report/build inputs or `results/submission/*` make the submission package STALE without falsely making the technical gate stale.
- Changes to committed experiment outputs are reported separately and require new experiment evidence only when the relevant experiment inputs/code/parameters have changed.

Acceptance:
- Positive and negative fixtures in `tests/test_provenance_consistency.py` pass.
- A source-change fixture fails technical freshness.
- A documentation-only fixture preserves technical freshness.
- A submission-binary-change fixture marks only package freshness stale.
- A retrospective migration snapshot is allowed to be committed after the historical evidence commit without rewriting history.

## P1 — Improve experimental depth and result validity

### P1.1 — Blue 3 parameter sensitivity and ablation

**Inspect/modify:**
- `src/blue3/analyze.py`
- `src/solve_challenges.py`
- `src/experiments/blue3_extended_robustness.py`
- `src/experiments/robustness_metrics.py`
- `tests/test_blue3_solver.py`
- `results/blue3/extended_robustness/`
- `report/REPORT.md`

Tasks:
1. Identify the pixel-difference threshold, candidate-length assumptions and region-selection logic from source; document each assumption.
2. Design a deterministic parameter sweep for threshold/region and image geometry; freeze seeds and record all parameters.
3. Separate exact-match rate, candidate-generation rate, position accuracy, Levenshtein distance and normalized similarity.
4. Add ablations that disable one decision component at a time (e.g. candidate region, threshold, channel selection) while preserving all other settings.
5. Compare the custom implementation against the public reference solver on the same pinned artifact and fixed transformed inputs; report the implementation differences rather than assuming equivalence.
6. Add edge-case tests for unsupported dimensions, missing candidates, wrong candidate length and malformed image input.

Acceptance:
- Every run has command, input SHA-256, parameters, seed where applicable, JSON/CSV output and runtime if actually measured.
- Original `data/blue3/blue.png` remains byte-identical.
- Failures and partial recoveries are retained, not filtered out.
- Report conclusions are restricted to the tested artifact and transformations.

### P1.2 — Sleepy Alarm alignment and reference-free extraction

**Inspect/modify:**
- `src/audio_alignment.py`
- `src/sleepy_alarm/analyze.py`
- `src/solve_challenges.py`
- `src/experiments/sleepy_alarm_robustness_matrix.py`
- `tests/test_audio_alignment.py`
- `tests/test_sleepy_alarm_solver.py`
- `results/sleepy_alarm/`
- `report/REPORT.md`

Tasks:
1. Specify which parts of the decoder depend on the reference track and which parts are intrinsic to the target audio.
2. Build a reference-free synchronization experiment that estimates symbol period, message start, amplitude levels and separator boundaries from the target alone.
3. Keep reference-assisted decoding as a separate baseline; never merge its results with blind/reference-free results.
4. Sweep target/reference gain asymmetry, sample rate, channel selection, resampling, AWGN and offset independently.
5. Record alignment lag, normalized correlation, symbol count, separator precision/recall, BER, SER and exact-match separately.
6. Add failure tests for unequal channels, empty overlap, low correlation, silent input, malformed separator stream and wrong sample rate.

Acceptance:
- Each experiment states whether reference audio is used.
- The ground-truth string is used for scoring after extraction, not to construct the decoded payload.
- No blind-decoding claim unless a complete exact-match occurs without reference assistance.
- Existing original MP3 inputs remain byte-identical.

### P1.3 — Rebuild the steganalysis benchmark on independent data

**Inspect/modify:**
- `src/steganalysis.py`
- `src/experiments/steganalysis_benchmark.py`
- `tests/test_steganalysis.py`
- `results/steganalysis/`
- `references/REFERENCES.md`
- `report/REPORT.md`

Tasks:
1. Keep the present benchmark and its audio recall=0 as a baseline failure; do not tune its threshold on the same test set.
2. Define a corpus manifest with source, license/permission, carrier type, modality, payload method, transformation, label and SHA-256.
3. Split by source challenge/carrier family into train, validation and held-out test to prevent near-duplicate leakage.
4. Fit or select features/thresholds on training/validation only; freeze them before held-out evaluation.
5. Report confusion matrix, precision, recall, F1, FPR and per-modality results. Add confidence intervals when sample size supports them.
6. Include simple baselines and document why each feature should discriminate stego from benign carriers.
7. Add deterministic dataset-integrity and split-leakage tests.

Acceptance:
- Test samples are not derivatives of the same source samples used for training/threshold selection.
- Dataset provenance and hash manifest are complete.
- Held-out test is evaluated once after model/threshold freeze.
- Small-sample limitations and class imbalance are explicit.
- No real-world/general-purpose detector claim based only on the current constructed benchmark.

### P1.4 — Ablation, comparison and validity analysis

**Inspect/modify:**
- `report/REPORT.md`
- `docs/DEFENSE_QA.md`
- `references/REFERENCES.md`
- relevant experiment scripts and JSON/CSV outputs

Required additions:
- **Internal validity:** implementation bugs, alignment assumptions, threshold tuning, codec/resampling effects and possible leakage.
- **External validity:** only two official challenges; variants from one artifact are not independent samples.
- **Construct validity:** define what exact-match, BER, SER, separator precision/recall and detector recall actually measure.
- **Ablation:** remove one component at a time and compare to the full method.
- **Comparison:** compare against the public reference implementation or another documented baseline using the same artifact/input conditions.
- **Threat model:** attacker knowledge, access to original/reference media, transformations, detection objective and defender visibility.
- **Defense:** map each observed weakness to concrete detection/mitigation, residual risk and false-positive cost.

Acceptance:
- Every quantitative statement points to a committed JSON/CSV/log.
- Every comparison states that inputs and conditions are controlled or explains why they differ.
- Every generalization is bounded by the corpus actually measured.

## P2 — Improve repository and academic quality

### P2.1 — Reproducible environment and code hygiene

**Files:** `requirements.txt`, `scripts/check_environment.py`, `README.md`, `tests/`, all scripts under `src/` and `scripts/`

Tasks:
1. Check dependency ranges and record exact environment used for the verified gate.
2. Use repository-relative paths; remove machine-specific absolute paths.
3. Check missing-file, invalid-format, empty-input and dependency-error handling.
4. Confirm deterministic seeds and explicit CLI parameters.
5. Scan for secrets, personal machine paths, unused code and duplicate outputs.

Acceptance:
- A clean environment can install dependencies and run the documented commands.
- Errors are actionable; tests cover normal and failure paths.
- No secret or private local path is committed.

### P2.2 — Citation and figure audit

**Files:** `references/REFERENCES.md`, `report/REPORT.md`

Tasks:
1. Use one citation style consistently (IEEE is suitable).
2. Cite challenge descriptions, creator source, reference solver, tool documentation and non-obvious technical claims.
3. Verify every reference is actually used and every in-text citation has a reference entry.
4. Give each figure a number, meaningful caption, source/experiment reference and interpretation in text.
5. Ensure no figure is merely decorative or unsupported by the reported experiment.

Acceptance:
- No uncited external writeup/code reuse.
- Captions and text explain what the figure demonstrates and what it does not demonstrate.

### P2.3 — Final submission package (separate from technical scoring)

**Files:** `scripts/build_submission.py`, `results/submission/`

Tasks:
1. Wait until report/source package contents are finalized.
2. Run `python scripts/build_submission.py --max-main-pages 17`.
3. Inspect PDF page count, rendering, figure legibility and citations.
4. List and inspect ZIP entries; verify source, tests, scripts, references, datasets and result evidence are present.
5. Exclude virtual environments, caches, secrets, nested ZIPs and stale outputs.
6. Record package build input commit and hashes in a separate package manifest; do not invent provenance from file timestamps alone.

Acceptance:
- DOCX/PDF/ZIP all derive from the same finalized content revision.
- The local PDF checker allows up to 17 main-content pages (appendix/references excluded). This project-level allowance does not override the 15-page course-guide guidance; if that is a strict submission cap, reduce the body to 15 pages before submitting.
- ZIP can be extracted and its contents verified.
- The checker reports package freshness only when a real build record exists.

## Recommended execution order

1. P0.1 and P0.2 are complete for tested source revision `38fbecab7aea8c241243fb50d044aea90ab657f7`; 38/38 gate evidence is committed.
2. Run P0 strict provenance validation on the checkout after this docs-only update; no full gate rerun is needed unless technical inputs changed.
3. P0.3 stale/freshness behavior is covered by the provenance regression suite included in the 38-test run.
4. P1.1 Blue 3 sensitivity/ablation.
5. P1.2 Sleepy Alarm reference-free synchronization.
6. P1.3 independent steganalysis corpus and held-out detector benchmark.
7. P1.4 integrate comparison, threat model and validity analysis into report/Q&A.
8. P2.1/P2.2 code, citation and figure audit.
9. P2.3 rebuild and inspect DOCX/PDF/ZIP once, at the end.

Do not treat this roadmap as evidence that future experiments have already been run. Mark each item complete only after its acceptance evidence is committed.
