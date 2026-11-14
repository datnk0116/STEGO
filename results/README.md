# Results and evidence

All committed results must be produced by a recorded run. Use a dated folder such as `results/2026-11-14/` or the stable challenge folders below.

## Required files

- `environment.json`: OS, architecture, Python and dependency versions.
- `artifact_manifest.json`: upstream URL, filename, byte size and SHA-256 for every input.
- `logs/unit-tests.log`: synthetic regression test output.
- `blue3/analysis.json`: image metadata and channel statistics.
- `blue3/figures/`: RGB histograms, pixel-difference heatmap and diagonal-region totals.
- `blue3/robustness/blue3_robustness.csv`: measured decoder results after JPEG/resize.
- `sleepy_alarm/analysis.json`: audio metadata, alignment, STFT and ASK envelope measurements.
- `sleepy_alarm/*.png`: waveform, spectrogram, carrier envelope and aligned residual plots.
- `sleepy_alarm/solver.json`: decoded text, symbol counts, cluster centers, byte errors and exact expected-text comparison.
- `sleepy_alarm/robustness/sleepy_alarm_robustness.csv` and `.json`: paired target/reference transform tests, only after baseline succeeds.\n- `sleepy_alarm/asymmetric_robustness/asymmetric_robustness.csv` and `.json`: target-only/reference-only transform tests, including decoded text, errors, clipping and alignment correlation.
- `logs/commands.log`: exact commands and standard output/error.
- `logbook-template.csv`: blank template; copy it to a dated logbook and record actual work sessions.

## Integrity and interpretation

Do not label a run successful because a string merely matches a flag prefix/suffix. For Sleepy Alarm, the verified run must match the full independently extracted 39-character value from the official generator bitmap. Keep both failed and successful attempts.

Never invent runtimes, metrics, screenshots or activity durations. If a metric has not been measured, mark it pending. The historical failed attempt in `2026-11-14/initial-run.md` must not be confused with the later verified final solver output.
