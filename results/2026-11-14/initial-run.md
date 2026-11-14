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

Initial analyzer attempt reported that the sample rate, frame count and channel count did not match. The audio alignment module has since been added. It resamples the reference if needed, estimates sample lag through cross-correlation, and limits subtraction to aligned overlap.

**Pending:** rerun the analyzer and ASK decoder with the updated alignment module, then record metadata, alignment score/lag, residual envelope levels, decoded bytes and validation. Do not claim successful audio extraction until this run succeeds.
