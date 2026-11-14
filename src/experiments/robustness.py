#!/usr/bin/env python3
"""Controlled perturbation helpers; always write to a separate output directory."""
from __future__ import annotations
import argparse, json
from fractions import Fraction
from pathlib import Path
from PIL import Image
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

def image_experiments(src: Path, out: Path) -> list[dict]:
    out.mkdir(parents=True, exist_ok=True)
    records=[]
    with Image.open(src) as im:
        rgb=im.convert("RGB")
        # JPEG recompression, then decode back to RGB; this is destructive to
        # pixel-level encoding and is deliberately performed only on copies.
        for quality in (95, 85, 70):
            target=out/f"blue_q{quality}.jpg"
            rgb.save(target, format="JPEG", quality=quality)
            records.append({"type":"jpeg","quality":quality,"output":str(target)})
        for scale in (0.75, 0.5):
            size=(max(1,round(rgb.width*scale)),max(1,round(rgb.height*scale)))
            target=out/f"blue_resize_{scale}.png"
            rgb.resize(size).save(target)
            records.append({"type":"resize","scale":scale,"output":str(target),"size":list(size)})
    return records

def audio_experiments(src: Path, out: Path) -> list[dict]:
    out.mkdir(parents=True, exist_ok=True)
    x,sr=sf.read(src,always_2d=True,dtype="float64")
    records=[]
    # Resample to 48 kHz and back to the original rate using polyphase filters.
    to_48k = Fraction(48000, sr).limit_denominator(100000)
    y=resample_poly(x, up=to_48k.numerator, down=to_48k.denominator, axis=0)
    back_to_source = Fraction(sr, 48000).limit_denominator(100000)
    y=resample_poly(y, up=back_to_source.numerator, down=back_to_source.denominator, axis=0)
    y_sr=sr
    target=out/"audio_resample_roundtrip.wav"
    sf.write(target,y,y_sr,subtype="PCM_24")
    records.append({"type":"resample_roundtrip","source_rate":sr,"intermediate_rate":48000,"output":str(target),"frames":int(y.shape[0])})
    for gain in (0.5, 1.5):
        target=out/f"audio_gain_{gain}.wav"
        sf.write(target,np.clip(x*gain,-1,1),sr,subtype="PCM_24")
        records.append({"type":"gain_and_clip","gain":gain,"output":str(target)})
    return records

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="kind",required=True)
    i=sub.add_parser("image"); i.add_argument("input",type=Path); i.add_argument("--out",type=Path,default=Path("results/robustness/image"))
    a=sub.add_parser("audio"); a.add_argument("input",type=Path); a.add_argument("--out",type=Path,default=Path("results/robustness/audio"))
    args=p.parse_args()
    if not args.input.is_file(): p.error(f"input does not exist: {args.input}")
    rows=image_experiments(args.input,args.out) if args.kind=="image" else audio_experiments(args.input,args.out)
    print(json.dumps(rows,indent=2))
    print("NOTE: Run the corresponding solver/analyzer on these copies and record actual success/failure; this script does not claim robustness results.")
    return 0
if __name__=="__main__": raise SystemExit(main())
