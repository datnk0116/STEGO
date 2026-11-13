# Challenge artifacts

Do not commit challenge binaries until licensing and repository size have been reviewed. Keep downloaded originals unchanged.

## Blue 3 — BYUCTF

Upstream: https://github.com/BYU-CSA/old-ctf-challenges/tree/master/forensics-steganography/blue-3

Download the official image to `data/blue3/blue.png`. Record the exact raw URL, upstream revision, retrieval date, byte size, image dimensions/mode and SHA-256. Do not recreate or substitute the file if unavailable.

## Sleepy Alarm — ImaginaryCTF 2024

Upstream: https://github.com/ImaginaryCTF/ImaginaryCTF-2024-Challenges/tree/main/Forensics/Sleepy%20Alarm

Download the official audio file to `data/sleepy_alarm/`, preserving its filename and extension. Record raw URL, revision, retrieval date, byte size, SHA-256, codec/container, sample rate, channels, frame count and duration.

## Integrity

```bash
shasum -a 256 data/blue3/blue.png
shasum -a 256 data/sleepy_alarm/*
```

Never overwrite originals with converted, filtered, normalized or resampled copies.