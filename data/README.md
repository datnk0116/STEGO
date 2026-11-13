# Challenge artifacts

Do not commit challenge binaries until licensing and repository size have been reviewed. Keep downloaded originals unchanged.

## Blue 3 — BYUCTF

Upstream: https://github.com/BYU-CSA/old-ctf-challenges/tree/master/forensics-steganography/blue-3

Official file: `blue.png` (upstream Git blob SHA `1dc26a1dde421a6ed0a553c89256e0ad75394c6b`, 9,406 bytes). Download from https://raw.githubusercontent.com/BYU-CSA/old-ctf-challenges/18c8f246756e79069c1cb1753c8bfea5e73e31f5/forensics-steganography/blue-3/blue.png to `data/blue3/blue.png`. The challenge README, creator source, and solver are in the same upstream directory. Record local SHA-256 and dimensions after download.

## Sleepy Alarm — ImaginaryCTF 2024

Upstream: https://github.com/ImaginaryCTF/ImaginaryCTF-2024-Challenges/tree/main/Forensics/Sleepy%20Alarm

Official distributed file: `morning_n_breakfast.mp3` (upstream Git blob SHA `5140f9652af9848374263dca3fdfcd9469903c4d`, 179,283 bytes). Download from https://raw.githubusercontent.com/ImaginaryCTF/ImaginaryCTF-2024-Challenges/21ea0e040638b953f5cc0efca1d900024899a7bc/Forensics/Sleepy%20Alarm/togive/morning_n_breakfast.mp3. The repository also contains `morning_n_breakfast_original.mp3` and `src/createsignal.m`, useful for comparative analysis. Record local SHA-256, codec/container, sample rate, channels, frame count and duration.

## Integrity

```bash
shasum -a 256 data/blue3/blue.png
shasum -a 256 data/sleepy_alarm/*
```

Never overwrite originals with converted, filtered, normalized or resampled copies.