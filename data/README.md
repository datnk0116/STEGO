# Challenge artifacts

The three official artifacts are committed under `data/` for reproducibility. Preserve their exact bytes; do not overwrite them with converted or transformed variants. The download script verifies upstream byte sizes and skips existing files.

## Blue 3 — BYUCTF

Upstream: https://github.com/BYU-CSA/old-ctf-challenges/tree/master/forensics-steganography/blue-3

Official file: `blue.png` (upstream Git blob SHA `1dc26a1dde421a6ed0a553c89256e0ad75394c6b`, 9,406 bytes). Download from https://raw.githubusercontent.com/BYU-CSA/old-ctf-challenges/18c8f246756e79069c1cb1753c8bfea5e73e31f5/forensics-steganography/blue-3/blue.png to `data/blue3/blue.png`. The challenge README, creator source, and solver are in the same upstream directory. Locally observed SHA-256: `009dab85bf6ccc5b42b8efa5f959ab6efa0c556b37eb6b4a77a21ec3356b721e`. Dimensions: 512 × 512, RGB.

## Sleepy Alarm — ImaginaryCTF 2024

Upstream: https://github.com/ImaginaryCTF/ImaginaryCTF-2024-Challenges/tree/main/Forensics/Sleepy%20Alarm

Official distributed file: `morning_n_breakfast.mp3` (upstream Git blob SHA `5140f9652af9848374263dca3fdfcd9469903c4d`, 179,283 bytes). Download from https://raw.githubusercontent.com/ImaginaryCTF/ImaginaryCTF-2024-Challenges/21ea0e040638b953f5cc0efca1d900024899a7bc/Forensics/Sleepy%20Alarm/togive/morning_n_breakfast.mp3. The repository also contains `morning_n_breakfast_original.mp3` and `src/createsignal.m`, useful for comparative analysis. Locally observed SHA-256: distributed file `bd181876c2d28152b9c3982fd88945d4e681fd93d49477622ea5841a3ff25ae2`; reference file `d0c283834955e54d68b0bba723ccd194142a428d2de74722e5f1dff3ccbd94ad2`. Record decoded codec/container, sample rate, channel count, frame count and duration in each run's JSON.

## Integrity

```bash
shasum -a 256 data/blue3/blue.png
shasum -a 256 data/sleepy_alarm/*
```

Never overwrite originals with converted, filtered, normalized or resampled copies.