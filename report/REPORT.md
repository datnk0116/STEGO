# UET.CN3124 — Steganography CTF Project

## 1. Topic and objectives
This project studies Blue 3 (image steganography) and Sleepy Alarm (audio steganography). The objectives are to identify the embedding mechanism, implement extraction, validate against the challenge format and evaluate limitations.

## 2. Background
Steganography hides a message in a carrier. Image carriers may encode information in pixel values; audio carriers may encode information in signal amplitude. Steganalysis seeks evidence of embedding and is distinct from successful decoding.

## 3. Environment
Python 3, NumPy, Pillow, SciPy and SoundFile. Install using requirements.txt. The workflow is offline and uses the committed official challenge artifacts.

## 4. Method
### Blue 3
Estimate the dominant RGB colour as the baseline. For each candidate payload length, partition diagonal image regions and sum channel differences to obtain character values. Accept only a candidate matching the BYUCTF flag format.
### Sleepy Alarm
Measure coherent amplitude at 8 kHz in 50-baud symbol windows. In reference-assisted mode, resample and align the original audio, subtract it from the distributed recording, then cluster three amplitude levels into separator, zero and one. Convert groups of eight bits into characters.

## 5. Reproduction
Follow the exact setup and CLI commands in README.md. Run the unit tests against the committed data files. Reference-assisted Sleepy Alarm must be labelled as reference-assisted.

## 6. Results
The integration tests check exact flags from both official artifacts. Record actual command output and environment when executing the tests; do not report unexecuted results as measured evidence.

## 7. Attacker and defender perspectives
An attacker who knows the carrier parameters and has the original audio can isolate a low-amplitude payload by subtraction. A defender can protect source media, compare against trusted originals, and inspect pixel or narrow-band signal anomalies. These are challenge-specific techniques, not universal detection methods.

## 8. Limitations and reflection
Sleepy Alarm depends on a reference recording for reliable extraction. Its decoder assumes carrier frequency, symbol rate, channel placement and transmission duration. Blue 3 assumes the dominant colour is the cover baseline and the payload follows the challenge's diagonal layout. Complete the personal reflection with your own verified observations; do not invent experience.
