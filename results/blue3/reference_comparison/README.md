# Blue 3 upstream reference cross-check

- Official upstream repository: https://github.com/BYU-CSA/old-ctf-challenges
- Upstream commit: `18c8f246756e79069c1cb1753c8bfea5e73e31f5`
- Solver source: `forensics-steganography/blue-3/solve.py`
- Official artifact: `data/blue3/blue.png`
- Artifact SHA-256: `009dab85bf6ccc5b42b8efa5f959ab6efa0c556b37eb6b4a77a21ec3356b721e`
- Dimensions: 512 × 512 RGB
- Local solver's committed output: `results/logs/blue3-solver.log`
- Runtime cross-check in this editing session: **NOT_RUN**. Source was inspected through the GitHub connector; this session did not have a local repository working tree/binary execution path. No upstream runtime, timing or output is claimed.

## Source-level comparison

| Property | BYUCTF upstream | STEGO local solver |
|---|---|---|
| Cover color | Modal RGB triplet via `Counter` | Modal RGB triplet via `numpy.unique` |
| Candidate lengths | 2 through image width | 2 through `min(width, height)`, optional max length |
| Region geometry | Floor-divided width/height, diagonal square per index | Same floor-divided diagonal square geometry |
| Character value | Sum signed differences across R/G/B | Same sum across R/G/B |
| Candidate acceptance | `re.match` against BYUCTF pattern | Anchored full-string regex |
| Input assumptions | Pillow-openable image, RGB conversion; no square-image assertion | Pillow-openable image, RGB conversion; no square-image assertion |
| Failure behavior | Exhausts width without candidate; no explicit malformed-file recovery | CLI reports candidate/attempts and permits a narrower search bound |

The core decoding rule is functionally equivalent for the pinned 512 × 512 artifact when both identify the same modal color and candidate length. Geometry and regex differences matter for non-square images, lengths beyond the shorter edge, and valid prefixes followed by trailing characters.

## Run the real artifact comparison

```bash
python src/blue3/reference_comparison.py data/blue3/blue.png
```

The script fetches the original upstream `solve.py` from the immutable raw URL above, runs it in a temporary directory containing the same `blue.png` bytes, and then runs the local solver. It writes `comparison.json` and `comparison.log` with candidate outputs, lengths, local attempt count, input/source SHA-256 and environment. If network access or Pillow is unavailable, it writes a FAILED record with the real exception. The automated regression test injects a tiny offline fixture only to test the comparison harness; it is not counted as the official upstream run. No speed winner is inferred.
