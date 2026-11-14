#!/usr/bin/env python3
"""Evaluate Blue 3 decoder behavior under controlled image transformations."""
from __future__ import annotations
import argparse, csv, json, sys, time
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
from solve_challenges import solve_blue

def solve(path:Path):
    start=time.perf_counter()
    candidate,attempts=solve_blue(path)
    return candidate,len(attempts),time.perf_counter()-start

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("image",type=Path)
    p.add_argument("--out",type=Path,default=Path("results/blue3/robustness"))
    args=p.parse_args()
    if not args.image.is_file(): p.error(f"missing image: {args.image}")
    args.out.mkdir(parents=True,exist_ok=True)
    with Image.open(args.image) as im: original=im.convert("RGB")
    baseline,tries,elapsed=solve(args.image)
    if not baseline:
        raise RuntimeError("baseline decoder did not recover a candidate; do not run robustness test")
    rows=[{"variant":"original","candidate":baseline,"matches_baseline":True,
           "attempts":tries,"elapsed_seconds":elapsed}]
    for quality in (95,85,70):
        path=args.out/f"blue_jpeg_q{quality}.jpg"
        original.save(path,format="JPEG",quality=quality)
        candidate,n,t=solve(path)
        rows.append({"variant":f"jpeg_q{quality}","candidate":candidate,
                     "matches_baseline":candidate==baseline,"attempts":n,"elapsed_seconds":t})
    for scale in (0.75,0.5):
        size=(round(original.width*scale),round(original.height*scale))
        path=args.out/f"blue_resize_{scale}.png"
        original.resize(size).save(path)
        candidate,n,t=solve(path)
        rows.append({"variant":f"resize_{scale}","candidate":candidate,
                     "matches_baseline":candidate==baseline,"attempts":n,"elapsed_seconds":t})
    csv_path=args.out/"blue3_robustness.csv"
    with csv_path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"baseline_candidate":baseline,"results":rows,"csv":str(csv_path)},indent=2))
    print("Interpretation: a failure after lossy recompression/resizing demonstrates sensitivity of this pixel-sum encoding, not a universal property of all image steganography.")
    return 0
if __name__=="__main__": raise SystemExit(main())
