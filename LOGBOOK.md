# LOGBOOK — UET.CN3124 Steganography CTF

**Project:** Blue 3 (image) and Sleepy Alarm (audio)  
**Repository:** `datnk0116/STEGO`  
**Purpose:** chronological record of the work actually performed, commands reported as executed, observed outputs, and limitations.

> This logbook is an evidence record, not a plan. Entries below describe completed actions only. A result is marked successful only when the corresponding execution output was reported. No later implementation, visualization, or experiment is represented as already completed.

---

## Entry 00 — Environment setup

**Date:** 16 November 2026  
**Platform:** macOS, MacBook Air  
**Python:** 3.14.10  
**Environment:** `.venv`  
**pip:** upgraded from 26.2.2 to 26.3

The operator reported creating and activating the virtual environment, upgrading pip, installing the dependencies from `requirements.txt`, and generating a dependency freeze with `python -m pip freeze`.

Packages reported installed:

- NumPy 2.5.5
- Pillow 13.0.0
- SciPy 1.18.1
- SoundFile 0.14.0
- cffi 2.1.1
- pycparser 3.12
- typing-extensions 4.16.0

The operator also reported that imports of NumPy, Pillow, SciPy, and SoundFile succeeded.

**Observed outcome:** dependency installation and direct import checks completed without a reported error.

**Scope:** this confirms the reported environment setup and imports; it does not, by itself, validate either challenge decoder.

---

## Entry 01 — Blue 3 image extraction

**Date:** 16 November 2026  
**Input:** `data/blue3/blue.png`

**Command reported as executed:**

```bash
PYTHONPATH=src python -m stego blue3 data/blue3/blue.png
```

**Reported output:**

- Decoded flag: `byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}`
- Candidate length accepted: 50 characters
- `format_valid`: `true`
- Exit code: `0`

**Outcome:** successful extraction was reported.

**Interpretation:** the implemented Blue 3 extraction routine recovered a candidate accepted by the challenge flag-format check. The command output, rather than the flag text alone, is the relevant execution evidence.

---

## Entry 02 — Sleepy Alarm, reference-assisted extraction

**Date:** 16 November 2026  
**Target audio:** `data/sleepy_alarm/morning_n_breakfast.mp3`  
**Reference audio:** `data/sleepy_alarm/morning_n_breakfast_original.mp3`

**Command reported as executed:**

```bash
PYTHONPATH=src python -m stego sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3
```

**Reported output:**

- Decoded flag: `ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}`
- `format_valid`: `true`
- Symbol count: 350
- Separator count: 38
- Alignment lag: 1,729 samples
- Normalized correlation: 0.9998734358246231
- Target start sample: 1,729
- Amplitude cluster centers:
  - 0.00010346536568754544
  - 0.0019974891068537835
  - 0.00497272470857525
- Byte errors: none
- Exit code: `0`

**Outcome:** successful reference-assisted extraction was reported.

**Interpretation and limitation:** this run explicitly used the original recording as a reference for alignment/subtraction. It is therefore a reference-assisted result, not proof that the payload can be extracted blindly from the distributed audio alone.

---

## Entry 03 — Sleepy Alarm, reference-free extraction

**Date:** 16 November 2026  
**Target audio:** `data/sleepy_alarm/morning_n_breakfast.mp3`  
**Reference audio:** none

**Command reported as executed:**

```bash
PYTHONPATH=src python -m stego sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3
```

**Reported output:**

- Decoded fragment: `ictsl33p_Nauk_arm_224dcb2}`
- `format_valid`: `false`
- Symbol count: 350
- Separator count: 49
- Malformed byte groups: 20
- Alignment: not performed
- Exit code: `2`

**Outcome:** unsuccessful extraction.

**Interpretation:** without the reference recording, the current implementation did not recover a valid flag. This failure is retained as a separate experimental result and must not be described as a successful blind extraction.

---

## Entry 04 — Automated tests

**Date:** 16 November 2026

**Command reported as executed:**

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

**Reported output:**

- Tests run: 2
- Blue 3 integration test: passed
- Sleepy Alarm reference-assisted integration test: passed
- Runtime: 0.294 seconds
- Summary: `Ran 2 tests in 0.294s — OK`
- Exit code: `0`

**Outcome:** both tests in the current test suite passed.

**Scope:** the audio integration test covers reference-assisted extraction. The two passing tests do not contradict or erase the separate reference-free failure recorded in Entry 03.

---

## Entry 05 — Repository state and input integrity recorded during the experiment

**Date:** 16 November 2026

The operator supplied the following Git state from the local checkout:

- Branch: `rebuild/working-runnable`
- Commit observed at that time: `925d9db2a7a969cd30643e1a23bfdd2d124c5122`
- Remote tracking branch: `origin/rebuild/working-runnable`
- Working-tree status: `?? results/` (the results directory was untracked)

The operator also supplied these SHA-256 values:

| Input artifact | SHA-256 |
|---|---|
| `data/blue3/blue.png` | `009dab85bf6ccc5b42b8efa5f959ab6efa0c556b37eb6b4a77a21ec3356b721e` |
| `data/sleepy_alarm/morning_n_breakfast.mp3` | `bd181876c2d28152b9c3982fd88945d4e681fd93d49477622ea5841a3ff25ae2` |
| `data/sleepy_alarm/morning_n_breakfast_original.mp3` | `d0c283834955e54d68b0bba723ccd194142a428d2de74722e5f1dff3ccbd94ad` |

**Interpretation:** the three hashes identify the challenge input files used in the reported experiments. The `results/` directory was reported as untracked at the time; the Git status was not clean.

---

## Evidence provenance and repository audit

The execution details in Entries 00–05 are transcribed from terminal output and Git information supplied by the operator on 16 November 2026. The exact execution time was not supplied.

At the time this logbook was checked against the GitHub branch `rebuild/working-runnable` (HEAD `37b672cc2a8b2980be16cd07f77b7c1b173e635d`), the tracked repository tree did **not** contain the reported `results/` output files or visualization artifacts. The entries therefore record the operator-reported runs; they do not claim those raw output files are currently archived in this Git tree.

The later HEAD above is a repository documentation state, not the commit observed during the experiment in Entry 05. No experiment result is attributed to that later commit.

No screenshot, visualization, reference-free success, or additional test result is claimed in this logbook.
