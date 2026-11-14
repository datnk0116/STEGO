# Experimental run log — 2026-11-14

## Environment

- OS: macOS 15.7.4
- Architecture: arm64
- Python: 3.14.10
- Pillow: 13.0.0
- NumPy: 2.5.4
- SciPy: 1.18.1
- Matplotlib: 3.11.2
- SoundFile: 0.14.0

## Blue 3

Command:
```bash
python src/blue3/analyze.py data/blue3/blue.png
python src/solve_challenges.py blue3 data/blue3/blue.png
```

Observed:
- File: data/blue3/blue.png
- Size: 9,406 bytes (upstream record)
- SHA-256: 009dab85bf6ccc5b42b8efa5f959ab6efa0c556b37eb6b4a77a21ec3356b721e
- PNG / RGB / 512 × 512 / 262,144 pixels
- Metadata keys: []
- R: min 64, max 68, mean 64.00663375854492, std 0.09345379422886371, 5 unique values
- G: min 77, max 81, mean 77.00653076171875, std 0.09425359809012815, 5 unique values
- B: min 205, max 209, mean 205.00653457641602, std 0.09423309511716214, 5 unique values

Solver output:
```text
Candidate: byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}
Attempts: 49
Format validated: True
```

Interpretation: solver produced a candidate matching the official BYUCTF flag syntax. This is a real user-run result captured in the conversation. Runtime was not measured.

## Sleepy Alarm — artifact acquisition

- Distributed MP3: 179,283 bytes
- Distributed MP3 SHA-256: bd181876c2d28152b9c3982fd88945d4e681fd93d49477622ea5841a3ff25ae2
- Original MP3: 160,495 bytes
- Original MP3 SHA-256: d0c283834955e54d68b0bba723ccd194142a428d2de74722e5f1dff3ccbd94ad2

Initial analyzer attempt failed because the two MP3s did not have identical frame counts. The later solver run reported both at 44,100 Hz and two channels, with an aligned overlap of 438,912 frames and lag 1,729 samples (0.039206 s); normalized absolute correlation was 0.9998734.

The first decoder after alignment was not successful: it averaged the stereo channels, processed 497 symbols over 9.952653 seconds instead of the 350-symbol / 7-second ASK transmission, classified 161 separators, produced 17 NUL characters, and reported malformed byte groups. This output is recorded as a failed attempt, not a decoded flag.

The corrected decoder now selects channel 0, preserves the original target prefix excluded by alignment, limits processing to the first 7 seconds and clusters the three measured envelope levels. Synthetic ASK regression coverage has been added, including an aligned-offset case.

## Historical-run status and later verified evidence\n\nThis file intentionally preserves the initial failed attempt and is not the final run status. The later committed evidence is recorded separately:\n\n- `results/sleepy_alarm/solver.json`: 350/350 symbols, 38 separators, 39 decoded bytes and full ground-truth exact-match.\n- `results/logs/unit-tests.log`: six synthetic regression tests passed.\n- `results/sleepy_alarm/robustness/`: paired target/reference robustness outputs.\n- `results/sleepy_alarm/asymmetric_robustness/`: one-sided robustness JSON/CSV, with 3/6 variants passing.\n- `results/blue3/robustness/blue3_robustness.csv`: five transformed-image trials plus the original baseline.\n\nThe later result files are the source of truth for final metrics. This historical note does not claim that the pending command above was rerun at the time of the initial attempt, and it does not supply an unmeasured runtime.
