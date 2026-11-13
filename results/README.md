# Results and evidence

Create a dated directory for each run, e.g. `results/2026-11-14/`.

Required evidence:
- `environment.txt`: OS, architecture, Python and dependency versions.
- `artifact_manifest.txt`: upstream URL, retrieval date, filename, byte size and SHA-256.
- `commands.log`: exact commands and stdout/stderr.
- `blue3/`: image statistics, histograms, extraction trace and screenshots.
- `sleepy_alarm/`: audio metadata, waveform, spectrogram, analysis parameters and screenshots.
- `experiments.csv`: experiment ID, hypothesis, input hash, parameters, outcome, elapsed time and notes.

Do not add a flag, metric or success status without a corresponding reproducible run. Redact secrets and personal data from screenshots.