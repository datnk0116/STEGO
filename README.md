# STEGO — UET.CN3124

Clean runnable implementation for Blue 3 (image) and Sleepy Alarm (audio).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
PYTHONPATH=src python -m stego blue3 data/blue3/blue.png
PYTHONPATH=src python -m stego sleepy-alarm data/sleepy_alarm/morning_n_breakfast.mp3 --reference data/sleepy_alarm/morning_n_breakfast_original.mp3
PYTHONPATH=src python -m unittest discover -s tests -v
```

Sleepy Alarm extraction with the original track is reference-assisted, not blind. The original challenge files are immutable. The analysis is offline and limited to the two selected public challenges.
