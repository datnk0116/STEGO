#!/usr/bin/env python3
"""One-sided audio robustness matrix for the reference-assisted ASK decoder."""
from __future__ import annotations
import argparse,csv,json,tempfile,sys,time
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import butter,sosfiltfilt,resample_poly
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
from solve_challenges import solve_sleepy

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("audio",type=Path);p.add_argument("--reference",type=Path,required=True)
    p.add_argument("--expected",required=True)
    p.add_argument("--out",type=Path,default=Path("results/sleepy_alarm/robustness_matrix"))
    p.add_argument("--seed",type=int,default=20261114)
    args=p.parse_args()
    target,sr=sf.read(args.audio,always_2d=True,dtype="float64")
    reference,rsr=sf.read(args.reference,always_2d=True,dtype="float64")
    if sr!=rsr: raise ValueError("target/reference sample rates must match for this matrix")
    args.out.mkdir(parents=True,exist_ok=True);rng=np.random.default_rng(args.seed);rows=[]
    def evaluate(name,t,r,side):
        with tempfile.TemporaryDirectory(prefix="ask-matrix-") as tmp:
            tp=Path(tmp)/"target.wav";rp=Path(tmp)/"reference.wav"
            sf.write(tp,t,sr);sf.write(rp,r,rsr)
            start=time.perf_counter();result=solve_sleepy(tp,reference=rp,expected_text=args.expected)
            elapsed=time.perf_counter()-start
        rows.append({"variant":name,"transformed_side":side,"success":result["success"],
          "format_valid":result["format_valid"],"decoded_length":result["decoded_length"],
          "symbols":result["measured_symbol_count"],"separators":result["symbol_counts"]["separator"],
          "errors":json.dumps(result["errors"]),"alignment_correlation":result["reference_alignment"]["normalized_abs_correlation"],
          "elapsed_seconds":elapsed,"decoded_text":result["decoded_text"]})
    evaluate("baseline",target,reference,"none")
    for side in ("target","reference"):
        base=target if side=="target" else reference
        for gain in (0.25,0.5,0.75,1.25,1.5,1.75):
            changed=np.clip(base*gain,-1,1)
            evaluate(f"{side}_gain_{gain}",changed if side=="target" else target,
              changed if side=="reference" else reference,side)
        for snr_db in (30,20,10):
            power=float(np.mean(base**2));noise_power=power/(10**(snr_db/10))
            changed=base+rng.normal(0,np.sqrt(noise_power),base.shape)
            evaluate(f"{side}_awgn_snr_{snr_db}db",changed if side=="target" else target,
              changed if side=="reference" else reference,side)
        sos=butter(4,[7500,8500],btype="bandpass",fs=sr,output="sos")
        changed=sosfiltfilt(sos,base,axis=0)
        evaluate(f"{side}_bandpass_7p5_8p5khz",changed if side=="target" else target,
          changed if side=="reference" else reference,side)
        changed=resample_poly(base,160,147,axis=0)
        changed=resample_poly(changed,147,160,axis=0)[:len(base)]
        evaluate(f"{side}_resample_roundtrip_44k1_48k",changed if side=="target" else target,
          changed if side=="reference" else reference,side)
    with (args.out/"robustness_matrix.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    result={"seed":args.seed,"trial_count":len(rows),"pass_count":sum(bool(x["success"]) for x in rows),
      "results":rows,"warning":"Single-artifact exploratory matrix; not a population-level robustness estimate."}
    (args.out/"robustness_matrix.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"trial_count":len(rows),"pass_count":result["pass_count"],
      "csv":str(args.out/"robustness_matrix.csv")},indent=2))
if __name__=="__main__":main()
