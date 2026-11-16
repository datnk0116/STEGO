# Steganography CTF Project — UET.CN3124

## 1. Topic, context and objectives

This project studies two public Jeopardy-style CTF challenges under the steganography topic: Blue 3, which embeds information in an image, and Sleepy Alarm, which embeds information in an audio recording. The objectives are to explain the hiding mechanism, implement extraction, reproduce the results on the supplied artifacts, and critically evaluate assumptions and limitations.

## 2. Background

Steganography aims to conceal the presence of a message within an ordinary carrier. Image and audio data provide large spaces in which small signal modifications can encode information. Steganalysis is the complementary process of identifying or investigating possible hidden data. A successful decoder does not, by itself, constitute a general-purpose detector.

## 3. Experimental environment and artifacts

The implementation uses Python, NumPy, Pillow, SciPy and SoundFile. Exact dependency constraints are listed in `requirements.txt`. The experiments use the image and audio files committed under `data/`. The original challenge artifacts remain unchanged; generated outputs are separate from the source artifacts.

The reported execution environment was macOS on a MacBook Air with Python 3.14.10 and an activated `.venv`. The operator reported successful installation of the dependencies and successful direct imports of NumPy, Pillow, SciPy and SoundFile.

## 4. Methodology

### 4.1 Blue 3 — image-domain extraction

The decoder converts the input to RGB, estimates a dominant colour as a baseline, and examines candidate diagonal regions for possible message lengths. It aggregates the per-channel differences in each region to recover character values. A candidate is accepted only when it conforms to the challenge flag format. This method relies on the challenge's construction pattern and should not be generalized to arbitrary images.

### 4.2 Sleepy Alarm — audio-domain extraction

The decoder reads the distributed recording and, when provided, the original/reference recording. It resamples the reference when sample rates differ, estimates the relative time offset using cross-correlation, and subtracts the aligned signals. It then measures coherent energy at the documented 8 kHz carrier in 50-baud symbol windows. Three amplitude clusters are interpreted as separator, binary zero and binary one; groups of eight bits are converted to text.

The reference-assisted mode depends on access to the original recording. It is distinguished from reference-free extraction in the results below.

## 5. Reproducible workflow

The setup, CLI commands and test invocation are maintained in `README.md`. The exact commands reported as executed, together with their outcomes, are recorded in `LOGBOOK.md`. The expected flag is a validation target only; it is not used as extraction input.

## 6. Results

The following results were reported from local executions on 16 November 2026. Exit codes and metrics are transcribed from the operator-supplied terminal output.

### 6.1 Blue 3

Command:

```bash
PYTHONPATH=src python -m stego blue3 data/blue3/blue.png
```

The decoder returned:

```text
byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}
```

The accepted candidate had 50 characters, `format_valid` was `true`, and the process exited with code 0. This is a successful extraction for the supplied challenge image.

### 6.2 Sleepy Alarm — reference-assisted

Command:

```bash
PYTHONPATH=src python -m stego sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3
```

The decoder returned:

```text
ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}
```

The output reported `format_valid: true`, 350 symbols, 38 separators, no byte errors, an alignment lag of 1,729 samples, normalized correlation of 0.9998734358246231, and target start sample 1,729. The three amplitude cluster centers were 0.00010346536568754544, 0.0019974891068537835, and 0.00497272470857525. The process exited with code 0.

This is a successful **reference-assisted** extraction. It does not establish that the payload can be recovered without the original recording.

### 6.3 Sleepy Alarm — reference-free

Command:

```bash
PYTHONPATH=src python -m stego sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3
```

Without a reference recording, the decoder returned the fragment `ictsl33p_Nauk_arm_224dcb2}`, reported `format_valid: false`, counted 350 symbols and 49 separators, and reported 20 malformed byte groups. The process exited with code 2.

This run was unsuccessful. It is retained as a negative result and shows that the current implementation does not reliably recover the flag in reference-free mode.

### 6.4 Automated tests

Command:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The reported test run completed 2 tests in 0.294 seconds with the summary `OK` and exit code 0. The passing tests cover Blue 3 extraction and Sleepy Alarm reference-assisted extraction. They do not establish success for reference-free Sleepy Alarm extraction.

### 6.5 Input artifact integrity

The operator reported these SHA-256 hashes for the challenge inputs:

| Input artifact | SHA-256 |
|---|---|
| `data/blue3/blue.png` | `009dab85bf6ccc5b42b8efa5f959ab6efa0c556b37eb6b4a77a21ec3356b721e` |
| `data/sleepy_alarm/morning_n_breakfast.mp3` | `bd181876c2d28152b9c3982fd88945d4e681fd93d49477622ea5841a3ff25ae2` |
| `data/sleepy_alarm/morning_n_breakfast_original.mp3` | `d0c283834955e54d68b0bba723ccd194142a428d2de74722e5f1dff3ccbd94ad` |

These hashes identify the input artifacts used in the reported experiments.

## 7. Attacker and defender perspectives

An attacker who knows the embedding parameters and has access to the relevant source media may be able to isolate small modifications through differencing and signal analysis. A defender can preserve trusted originals, monitor media-processing pipelines, inspect unusual pixel/channel distributions, and examine suspicious narrow-band or symbol-period structures. These measures are challenge-specific; their false-positive rates and generalization have not been measured in these experiments.

## 8. Limitations and validity

Blue 3 assumes the dominant image colour is a suitable baseline and that the payload follows the expected diagonal layout. Sleepy Alarm assumes a known carrier frequency, symbol rate, channel choice and transmission duration. The successful Sleepy Alarm run also assumes access to the original recording for alignment and subtraction. The reference-free run failed, so the project does not claim blind recovery for this audio challenge.

The experiments cover two selected challenge artifacts and a two-test integration suite. They do not establish performance on arbitrary media or a general-purpose steganography detector. The results are valid for the supplied files and reported execution conditions; broader generalization would require additional samples and controlled parameter variation.

## 9. Reflection

The two challenges required different extraction strategies: image-channel differences for Blue 3 and time-aligned audio differencing followed by symbol-level amplitude classification for Sleepy Alarm. The reported runs show that the Blue 3 decoder and reference-assisted Sleepy Alarm decoder recovered format-valid flags, while the reference-free Sleepy Alarm run did not.

The failed reference-free run is a material limitation rather than a result to omit. It demonstrates that the successful audio extraction depends on the reference track under the current implementation. The passing integration tests are consistent with this scope because the audio test exercises the reference-assisted path. A more complete evaluation would require a separately validated reference-free method and additional test cases; neither is claimed as completed here.
