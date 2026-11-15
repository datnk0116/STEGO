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

Keep screenshots (PNG) in `evidence/`; keep raw terminal output, JSON and logs in `results/`. Suggested filenames:

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
after_dummy_command=true
mkdir -p evidence/01_environment evidence/02_blue3 evidence/03_sleepy_alarm evidence/04_tests evidence/05_final
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pip freeze > results/logs/environment-freeze.txt
```

Windows PowerShell: use `py -m venv .venv`, activate with `.\\.venv\\Scripts\\Activate.ps1`, and create folders using `New-Item -ItemType Directory -Force`. The remaining pip commands are the same.

**Screenshot:** show Python version, successful venv activation and dependency installation. Save as `evidence/01_environment/01_python_version.png`. Keep `results/logs/environment-freeze.txt` as the full dependency record.

**Log:** OS/version, Python version, environment method, dependency install status, warnings and errors.

## 3. Blue 3 run

```bash
PYTHONPATH=src python -m stego blue3 data/blue3/blue.png
```

Save full output:

```bash
PYTHONPATH=src python -m stego blue3 data/blue3/blue.png > results/blue3/decoder-output.txt 2>&1
```

Check exit code immediately: `echo $?` on macOS/Linux; `$LASTEXITCODE` in PowerShell.

**Screenshots:** command and input path → `evidence/02_blue3/01_command.png`; decoded output and `format_valid` → `evidence/02_blue3/02_result.png`.

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

**Screenshots:** two-file reference-assisted command → `evidence/03_sleepy_alarm/01_reference_assisted_command.png`; decoded text and symbol metrics → `evidence/03_sleepy_alarm/02_reference_assisted_result.png`; reference-free result → `evidence/03_sleepy_alarm/03_reference_free_result.png`.

**Log:** reference usage, input paths, alignment offset/correlation if printed, decoded text, symbol/separator counts, format validity, exit code and evidence locations.

## 5. Test suite

```bash
PYTHONPATH=src python -m unittest discover -s tests -v > results/logs/unittest.log 2>&1
```

Check exit code immediately (`echo $?` or `$LASTEXITCODE`).

**Screenshot:** show test names and final summary (`Ran ... tests`, `OK`, or failure traceback), save as `evidence/04_tests/01_unittest_summary.png`. Keep the full log even when tests fail.

**Log:** test count, pass/fail, duration when printed, exit code and failing test names.

## 6. Final integrity/status capture

```bash
git status --short --branch
git branch --show-current
git log -1 --oneline
shasum -a 256 data/blue3/blue.png data/sleepy_alarm/morning_n_breakfast.mp3 data/sleepy_alarm/morning_n_breakfast_original.mp3
```

On Linux use `sha256sum` instead of `shasum -a 256`.

Screenshot branch, latest commit and working-tree status as `evidence/05_final/01_git_status.png`. Expected uncommitted logbook/evidence changes are not a clean-tree result; state them accurately.

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

## 9. Required execution entries

### Entry 00 — Environment setup

Status: **PENDING — run Section 2 and fill the entry template.** Save screenshot in `evidence/01_environment/` and dependency freeze in `results/logs/`.

### Entry 01 — Blue 3

Status: **PENDING — run Section 3 and fill the entry template.** Save raw output in `results/blue3/` and screenshots in `evidence/02_blue3/`.

### Entry 02 — Sleepy Alarm, reference-assisted

Status: **PENDING — run Section 4.1 and fill the entry template.** Save JSON in `results/sleepy_alarm/` and screenshots in `evidence/03_sleepy_alarm/`.

### Entry 03 — Sleepy Alarm, reference-free

Status: **PENDING — run Section 4.2 and fill the entry template.** Do not merge its outcome with Entry 02.

### Entry 04 — Automated tests

Status: **PENDING — run Section 5 and fill the entry template.** Save `results/logs/unittest.log` and screenshot in `evidence/04_tests/`.

### Entry 05 — Final repository status

Status: **PENDING — run Section 6 and record branch, commit, artifact hashes and working-tree state.**

## 10. Evidence checklist

- [ ] Python version and dependency installation.
- [ ] Blue 3 command, output and exit code.
- [ ] Sleepy Alarm reference-assisted command, output and exit code.
- [ ] Sleepy Alarm reference-free command, output and exit code.
- [ ] Full test log and summary screenshot.
- [ ] Branch, commit and official artifact hashes.
- [ ] Every screenshot is linked from a logbook entry.
- [ ] Failed runs and debugging evidence are retained.
- [ ] Personal reflection in the report describes work actually performed.
