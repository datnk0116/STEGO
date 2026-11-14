#!/usr/bin/env python3
"""Extended Blue 3 attack matrix; each trial is non-destructive."""
from __future__ import annotations
import argparse,csv,json,sys,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageEnhance,ImageFilter
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
from solve_challenges import solve_blue

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("image",type=Path)
    p.add_argument("--out",type=Path,default=Path("results/blue3/extended_robustness"))
    p.add_argument("--seed",type=int,default=20261114)
    args=p.parse_args()
    if not args.image.is_file(): p.error(f"missing image: {args.image}")
    args.out.mkdir(parents=True,exist_ok=True)
    with Image.open(args.image) as im: original=im.convert("RGB")
    baseline,_=solve_blue(args.image)
    if not baseline: raise RuntimeError("baseline did not decode")
    rng=np.random.default_rng(args.seed)
    variants={
      "brightness_0.9":ImageEnhance.Brightness(original).enhance(0.9),
      "brightness_1.1":ImageEnhance.Brightness(original).enhance(1.1),
      "contrast_0.9":ImageEnhance.Contrast(original).enhance(0.9),
      "contrast_1.1":ImageEnhance.Contrast(original).enhance(1.1),
      "gaussian_blur_radius_0.3":original.filter(ImageFilter.GaussianBlur(0.3)),
      "crop_16px":original.crop((16,16,original.width-16,original.height-16))}
    arr=np.asarray(original,dtype=np.int16)
    for sigma in (0.5,1.0,2.0):
        variants[f"gaussian_noise_sigma_{sigma}"]=Image.fromarray(
          np.clip(arr+rng.normal(0,sigma,arr.shape),0,255).astype(np.uint8))
    rows=[]
    for name,image in variants.items():
        path=args.out/f"{name}.png";image.save(path)
        started=time.perf_counter();candidate,attempts=solve_blue(path);elapsed=time.perf_counter()-started
        rows.append({"variant":name,"success":candidate==baseline,"candidate":candidate,
          "attempts":len(attempts),"elapsed_seconds":elapsed})
    with (args.out/"extended_robustness.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    result={"baseline_success":True,"seed":args.seed,"variant_count":len(rows),
      "success_count":sum(r["success"] for r in rows),"results":rows,
      "warning":"Results characterize this decoder and exact attack settings only."}
    (args.out/"extended_robustness.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
