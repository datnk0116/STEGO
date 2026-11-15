# Steganography CTF Project — UET.CN3124

## 1. Topic, context and objectives

This project studies two public Jeopardy-style CTF challenges under the steganography topic: Blue 3, which embeds information in an image, and Sleepy Alarm, which embeds information in an audio recording. The objectives are to explain the hiding mechanism, implement extraction, reproduce the results on the supplied artifacts, and critically evaluate assumptions and limitations.

## 2. Background

Steganography aims to conceal the presence of a message within an ordinary carrier. Image and audio data provide large spaces in which small signal modifications can encode information. Steganalysis is the complementary process of identifying or investigating possible hidden data. A successful decoder does not, by itself, constitute a general-purpose detector.

## 3. Experimental environment and artifacts

The implementation uses Python, NumPy, Pillow, SciPy and SoundFile. Exact dependencies are listed in `requirements.txt`. The experiments use the image and audio files committed under `data/`. The original challenge artifacts should remain unchanged; derived data belongs under `results/`.

## 4. Methodology

### 4.1 Blue 3 — image-domain extraction

The decoder converts the input to RGB, estimates a dominant colour as a baseline, and examines candidate diagonal regions for possible message lengths. It aggregates the per-channel differences in each region to recover character values. A candidate is accepted only when it conforms to the challenge flag format. This method relies on the challenge's construction pattern and should not be generalized to arbitrary images.

### 4.2 Sleepy Alarm — audio-domain extraction

The decoder reads the distributed recording and, when provided, the original/reference recording. It resamples the reference when sample rates differ, estimates the relative time offset using cross-correlation, and subtracts the aligned signals. It then measures coherent energy at the documented 8 kHz carrier in 50-baud symbol windows. Three amplitude clusters are interpreted as separator, binary zero and binary one; groups of eight bits are converted to text.

The reference-assisted mode depends on access to the original recording. It must be distinguished from reference-free extraction in all results and discussion.

## 5. Reproducible workflow

The complete setup, CLI commands and test invocation are maintained in `README.md`. Each experiment should be recorded in `LOGBOOK.md`, including the exact command, environment, exit code, result and screenshot/log path. The expected flag is a validation target only; it must not be used as extraction input.

## 6. Results

Record only results reproduced by executing the commands against the committed artifacts. Include the full terminal output or saved JSON output and report whether each decoder produced a format-valid result. For Sleepy Alarm, state explicitly whether the reference track was used. Do not substitute expected values for measured outputs.

## 7. Attacker and defender perspectives

An attacker who knows the embedding parameters and has access to the relevant source media may be able to isolate small modifications through differencing and signal analysis. A defender can preserve trusted originals, monitor media-processing pipelines, inspect unusual pixel/channel distributions, and examine suspicious narrow-band or symbol-period structures. These measures are challenge-specific; their false-positive rates and generalization require separate evaluation.

## 8. Limitations and validity

Blue 3 assumes the dominant image colour is a suitable baseline and that the payload follows the expected diagonal layout. Sleepy Alarm assumes a known carrier frequency, symbol rate, channel choice and transmission duration. Reference-assisted subtraction is not a blind method. Results from two selected challenges cannot establish performance on arbitrary media or a general detector. Document any failed run, sensitivity to parameters, and threats to internal, construct and external validity.

## 9. Reflection

Complete this section after performing the experiments. Discuss what was personally observed, which assumptions were confirmed, what failed, how errors were diagnosed, and what would be improved. Do not include unperformed work or invented personal experience.
