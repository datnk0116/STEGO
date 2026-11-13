#!/usr/bin/env python3
"""Download pinned official CTF artifacts and verify their published byte sizes."""
from __future__ import annotations
import argparse, hashlib, urllib.request
from pathlib import Path

ARTIFACTS = {
    "blue3": (
        "https://raw.githubusercontent.com/BYU-CSA/old-ctf-challenges/18c8f246756e79069c1cb1753c8bfea5e73e31f5/forensics-steganography/blue-3/blue.png",
        Path("data/blue3/blue.png"), 9406,
    ),
    "sleepy-alarm-original": (
        "https://raw.githubusercontent.com/ImaginaryCTF/ImaginaryCTF-2024-Challenges/21ea0e040638b953f5cc0efca1d900024899a7bc/Forensics/Sleepy%20Alarm/src/morning_n_breakfast_original.mp3",
        Path("data/sleepy_alarm/morning_n_breakfast_original.mp3"), 160495,
    ),
    "sleepy-alarm": (
        "https://raw.githubusercontent.com/ImaginaryCTF/ImaginaryCTF-2024-Challenges/21ea0e040638b953f5cc0efca1d900024899a7bc/Forensics/Sleepy%20Alarm/togive/morning_n_breakfast.mp3",
        Path("data/sleepy_alarm/morning_n_breakfast.mp3"), 179283,
    ),
}
def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("artifact",choices=[*ARTIFACTS,"all"],default="all",nargs="?")
    p.add_argument("--force",action="store_true")
    args=p.parse_args()
    keys=list(ARTIFACTS) if args.artifact=="all" else [args.artifact]
    for key in keys:
        url,path,expected=ARTIFACTS[key]
        path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and not args.force:
            print(f"SKIP existing: {path} (use --force to replace)")
            continue
        request=urllib.request.Request(url,headers={"User-Agent":"STEGO-UETCN3124-research/1.0"})
        with urllib.request.urlopen(request,timeout=45) as response:
            data=response.read()
        if len(data)!=expected:
            raise RuntimeError(f"{key}: expected {expected} bytes, received {len(data)}; refusing to save")
        path.write_bytes(data)
        print(f"{key}: {path} bytes={len(data)} sha256={sha256(path)}")
    return 0
if __name__=="__main__": raise SystemExit(main())
