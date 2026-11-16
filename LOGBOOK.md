# LOGBOOK — UET.CN3124 Steganography Project

> Record only commands you actually executed and observations you actually saw. Do not invent results, runtimes, screenshots or PASS statuses.

## 1. Evidence layout

Create these directories at the repository root:

```text
evidence/
├── 01_environment/
├── 02_blue3/
├── 03_sleepy_alarm/
├── 04_tests/
└── 05_final/
results/
├── blue3/
├── sleepy_alarm/
└── logs/
```

Keep raw terminal output, JSON and logs in `results/`. Screenshots are optional supplementary evidence; they are not required when the full command and output have been preserved in terminal logs. Suggested filenames if screenshots are later requested:

- `evidence/01_environment/01_python_version.png`
- `evidence/02_blue3/01_command.png`
- `evidence/02_blue3/02_result.png`
- `evidence/03_sleepy_alarm/01_reference_assisted_command.png`
- `evidence/03_sleepy_alarm/02_reference_assisted_result.png`
- `evidence/03_sleepy_alarm/03_reference_free_result.png`
- `evidence/04_tests/01_unittest_summary.png`
- `evidence/05_final/01_git_status.png`

Add `_02`, `_03` for additional screenshots; never overwrite earlier evidence.

## 2. Checkout and environment

Run from the repository root:

```bash
git switch rebuild/working-runnable
git status --short --branch
git branch --show-current
git log -1 --oneline
python3 --version
mkdir -p results/blue3 results/sleepy_alarm results/logs
mkdir -p evidence/01_environment evidence/02_blue3 evidence/03_sleepy_alarm evidence/04_tests evidence/05_final
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pip freeze > results/logs/environment-freeze.txt
```

Windows PowerShell: use `py -m venv .venv`, activate with `.\\.venv\\Scripts\\Activate.ps1`, and create folders using `New-Item -ItemType Directory -Force`. The remaining pip commands are the same.

**Evidence:** the terminal transcript supplied by the operator is sufficient to record this setup. Keep `results/logs/environment-freeze.txt` as the dependency record. A screenshot is optional.

**Log:** OS/version if known, Python version, environment method, dependency install status, warnings and errors.

## 3. Blue 3 run

```bash
PYTHONPATH=src python -m stego blue3 data/blue3/blue.png
```

Save full output:

```bash
PYTHONPATH=src python -m stego blue3 data/blue3/blue.png > results/blue3/decoder-output.txt 2>&1
```

Check exit code immediately: `echo $?` on macOS/Linux; `$LASTEXITCODE` in PowerShell.

**Evidence:** preserve `results/blue3/decoder-output.txt`. The complete terminal output supplied by the operator is sufficient; no screenshot is required.

**Log:** exact command, date/time, exit code, decoded candidate, format validity, output path, screenshot paths and any debugging notes. Never insert an expected flag as if it were program output.

## 4. Sleepy Alarm runs

### 4.1 Reference-assisted

```bash
PYTHONPATH=src python -m stego sleepy-alarm \\
  data/sleepy_alarm/morning_n_breakfast.mp3 \\
  --reference data/sleepy_alarm/morning_n_breakfast_original.mp3 \\
  > results/sleepy_alarm/reference-assisted-output.json 2>&1
```

### 4.2 Reference-free

```bash
PYTHONPATH=src python -m stego sleepy-alarm \\
  data/sleepy_alarm/morning_n_breakfast.mp3 \\
  > results/sleepy_alarm/reference-free-output.json 2>&1
```

These are distinct experiments. The first uses the original recording to align and subtract the signal; it is not blind extraction. Record the second separately and preserve failure output.

**Evidence:** preserve `results/sleepy_alarm/reference-assisted-output.json` and `results/sleepy_alarm/reference-free-output.json`. The terminal transcripts are sufficient; screenshots are optional.

**Log:** reference usage, input paths, alignment offset/correlation if printed, decoded text, symbol/separator counts, format validity, exit code and evidence locations.

## 5. Test suite

```bash
PYTHONPATH=src python -m unittest discover -s tests -v > results/logs/unittest.log 2>&1
```

Check exit code immediately (`echo $?` or `$LASTEXITCODE`).

**Evidence:** preserve `results/logs/unittest.log`. The complete terminal transcript is sufficient; no screenshot is required.

**Log:** test count, pass/fail, duration when printed, exit code and failing test names.

## 6. Final integrity/status capture

```bash
git status --short --branch
git branch --show-current
git log -1 --oneline
shasum -a 256 data/blue3/blue.png data/sleepy_alarm/morning_n_breakfast.mp3 data/sleepy_alarm/morning_n_breakfast_original.mp3
```

On Linux use `sha256sum` instead of `shasum -a 256`.

A screenshot is optional. Record the actual branch, commit and working-tree status in this logbook. Expected uncommitted logbook/evidence changes are not a clean-tree result; state them accurately.

## 7. Screenshot standards

- Capture the real terminal/editor after the command finishes.
- macOS: `Shift + Command + 4` or `Shift + Command + 5`.
- Windows: `Win + Shift + S`.
- Keep command, input file and result visible and readable.
- Do not fabricate, recreate or edit terminal text. Cropping is acceptable only when relevant context remains.
- Do not expose tokens, passwords or unrelated personal information.
- Store images under the matching `evidence/` folder; store raw outputs under `results/`.
- Preserve failed runs and tracebacks. Failed experiments are valid evidence when documented honestly.

## 8. Entry template — copy for every execution

### Entry [NN] — [experiment title]

| Field | Record |
|---|---|
| Date/time and timezone | |
| Operator | |
| Branch / commit | |
| OS / Python | |
| Objective | |
| Input artifact(s) | |
| Exact command | |
| Parameters / reference use | |
| Exit code | |
| Actual output / observation | |
| PASS/FAIL criterion | |
| Error and debugging notes | |
| Raw output path | |
| Screenshot path(s) | |

**Interpretation:** what does this result demonstrate, and what does it not demonstrate?

**Next action:** one concrete action based on this run.

---

## 9. Actual execution record — 16 November 2026

The entries below are based on the terminal transcript supplied by the operator. The operator ran the commands locally on a MacBook Air. The exact macOS release, Git branch, current commit SHA and artifact hashes were not included in the transcript and are therefore left unasserted.

### Entry 00 — Environment setup

| Field | Recorded result |
|---|---|
| Date | 16 November 2026 (exact execution time not provided) |
| Platform | macOS on MacBook Air; Apple Silicon is consistent with the downloaded `arm64` wheels |
| Python | 3.14.10 |
| Virtual environment | `.venv`, activated successfully |
| pip | Upgraded from 26.2.2 to 26.3 |
| Dependencies | Installed successfully from `requirements.txt` |
| Installed packages | NumPy 2.5.5; Pillow 13.0.0; SciPy 1.18.1; SoundFile 0.14.0; cffi 2.1.1; pycparser 3.12; typing-extensions 4.16.0 |
| Import check | `All dependencies imported successfully` |
| Result | **PASS** |
| Dependency record | `results/logs/environment-freeze.txt` was generated by `pip freeze` |

**Observation:** all four direct imports (NumPy, Pillow, SciPy and SoundFile) succeeded under Python 3.14.10. Package installation completed without a reported error.

**Interpretation:** the selected environment can install the declared dependencies and import the libraries required by the project. This alone does not establish that every challenge decoder works; those are validated in the following entries.

### Entry 01 — Blue 3 image extraction

| Field | Recorded result |
|---|---|
| Input | `data/blue3/blue.png` |
| Command | `PYTHONPATH=src python -m stego blue3 data/blue3/blue.png` (stdout/stderr redirected to `results/blue3/decoder-output.txt`) |
| Exit code | 0 |
| Decoded flag | `byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}` |
| Format validation | `true` |
| Candidate length | 50 characters |
| Result | **PASS** |
| Raw output | `results/blue3/decoder-output.txt` |

**Observation:** the decoder evaluated candidate lengths and accepted the 50-character candidate matching the BYUCTF flag format. The output also showed intermediate candidates for other lengths; those were rejected.

**Interpretation:** the implemented diagonal-region pixel-difference method successfully recovered the hidden text from the supplied Blue 3 image. Exit code 0 and `format_valid: true` provide direct execution evidence.

### Entry 02 — Sleepy Alarm, reference-assisted extraction

| Field | Recorded result |
|---|---|
| Target audio | `data/sleepy_alarm/morning_n_breakfast.mp3` |
| Reference audio | `data/sleepy_alarm/morning_n_breakfast_original.mp3` |
| Mode | Reference-assisted |
| Command | `PYTHONPATH=src python -m stego sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3` |
| Exit code | 0 |
| Decoded text | `ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}` |
| Format validation | `true` |
| Symbols measured | 350 |
| Separators | 38 |
| Alignment lag | 1,729 samples |
| Normalized correlation | 0.9998734358246231 |
| Target start sample | 1,729 |
| Amplitude cluster centers | 0.00010346536568754544; 0.0019974891068537835; 0.00497272470857525 |
| Byte errors | None |
| Result | **PASS** |
| Raw output | `results/sleepy_alarm/reference-assisted-output.json` |

**Observation:** after aligning and subtracting the reference recording, the decoder measured 350 symbols, identified 38 separators and decoded the complete 39-character flag. No malformed byte groups were reported.

**Interpretation:** the result demonstrates successful reference-assisted extraction for this challenge artifact. It does not demonstrate blind extraction because the original recording was explicitly supplied.

### Entry 03 — Sleepy Alarm, reference-free extraction

| Field | Recorded result |
|---|---|
| Target audio | `data/sleepy_alarm/morning_n_breakfast.mp3` |
| Reference audio | None |
| Mode | Reference-free |
| Command | `PYTHONPATH=src python -m stego sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3` |
| Exit code | 2 |
| Decoded text fragment | `ictsl33p_Nauk_arm_224dcb2}` |
| Format validation | `false` |
| Symbols measured | 350 |
| Separators | 49 |
| Malformed byte groups | 20 |
| Alignment | Not performed |
| Result | **FAIL — expected limitation / unsuccessful extraction in this mode** |
| Raw output | `results/sleepy_alarm/reference-free-output.json` |

**Observation:** without the reference track, the decoder produced an incomplete/corrupted text fragment and reported 20 byte groups whose lengths were not eight bits. The output had `format_valid: false` and exit code 2.

**Interpretation:** this experiment shows that the current implementation does not reliably recover the payload from the distributed audio alone. The successful Sleepy Alarm result must therefore be reported as reference-assisted. This negative result is important and must not be hidden or merged with Entry 02.

### Entry 04 — Automated test suite

| Field | Recorded result |
|---|---|
| Command | `PYTHONPATH=src python -m unittest discover -s tests -v` |
| Tests run | 2 |
| Blue 3 integration test | PASS |
| Sleepy Alarm reference-assisted integration test | PASS |
| Runtime | 0.294 seconds |
| Summary | `Ran 2 tests in 0.294s — OK` |
| Exit code | 0 |
| Result | **PASS** |
| Raw output | `results/logs/unittest.log` |

**Observation:** both integration tests completed successfully. The audio test explicitly tests the reference-assisted mode.

**Interpretation:** the current test suite validates the Blue 3 result and the reference-assisted Sleepy Alarm result on the supplied artifacts. It does not assert that reference-free Sleepy Alarm extraction succeeds; that limitation is recorded separately in Entry 03.

### Entry 05 — Git state and artifact integrity

**Status: PENDING.** The supplied terminal transcript does not include `git status`, `git branch --show-current`, `git log -1` or artifact SHA-256 output. Run Section 6 and append the actual values before declaring the repository state verified.

## 10. Remaining evidence and documentation checklist

- [x] Python 3.14.10 and dependency installation recorded.
- [x] Blue 3 command, decoded output, format validation and exit code recorded.
- [x] Sleepy Alarm reference-assisted command, decoded output, alignment metrics and exit code recorded.
- [x] Sleepy Alarm reference-free failure and exit code recorded.
- [x] Unit test results (2 passed) recorded.
- [ ] Git branch, latest commit and working-tree status recorded.
- [ ] SHA-256 hashes of all three input artifacts recorded.
- [ ] Confirm the local output files exist and match the supplied terminal transcript.
- [ ] Complete the report's personal reflection based on the actual debugging and execution experience.

**Screenshot policy:** screenshots are not mandatory for these entries because the operator supplied complete command transcripts and outputs. Raw terminal logs and machine-readable output files are the primary evidence. Add screenshots only if the course submission rubric or instructor explicitly requires them.
