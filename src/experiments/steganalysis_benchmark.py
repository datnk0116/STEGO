#!/usr/bin/env python3
"""Run a reproducible, explicitly synthetic benign-vs-challenge triage benchmark."""
from __future__ import annotations
import argparse, csv, json, sys, tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from steganalysis import analyze
from solve_challenges import solve_sleepy


def confusion(rows):
    tp=sum(r["label"]=="stego" and r["predicted"] for r in rows)
    tn=sum(r["label"]=="benign" and not r["predicted"] for r in rows)
    fp=sum(r["label"]=="benign" and r["predicted"] for r in rows)
    fn=sum(r["label"]=="stego" and not r["predicted"] for r in rows)
    precision=tp/(tp+fp) if tp+fp else 0.0
    recall=tp/(tp+fn) if tp+fn else 0.0
    return {"tp":tp,"tn":tn,"fp":fp,"fn":fn,"precision":precision,
            "recall":recall,"f1":2*precision*recall/(precision+recall) if precision+recall else 0.0,
            "false_positive_rate":fp/(fp+tn) if fp+tn else 0.0}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--blue3",type=Path,default=Path("data/blue3/blue.png"))
    p.add_argument("--sleepy",type=Path,default=Path("data/sleepy_alarm/morning_n_breakfast.mp3"))
    p.add_argument("--reference",type=Path,default=Path("data/sleepy_alarm/morning_n_breakfast_original.mp3"))
    p.add_argument("--expected",default="ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}")
    p.add_argument("--out",type=Path,default=Path("results/steganalysis"))
    args=p.parse_args()
    for path in (args.blue3,args.sleepy,args.reference):
        if not path.is_file(): p.error(f"missing challenge artifact: {path}")
    args.out.mkdir(parents=True,exist_ok=True)
    rows=[]
    def add(path,kind,label,source):
        result=analyze(path,kind)
        rows.append({"sample":path.name,"kind":kind,"label":label,
                     "predicted":result["flagged"],"source":source,
                     "features_json":json.dumps(result["features"],sort_keys=True),
                     "reasons":";".join(result["reasons"])})
    with tempfile.TemporaryDirectory(prefix="stego-benchmark-") as tmp:
        d=Path(tmp)
        # Deterministic synthetic controls. These are not real-world benign data.
        rng=np.random.default_rng(20261114)
        for i in range(8):
            arr=rng.integers(0,256,size=(256,256,3),dtype=np.uint8)
            path=d/f"benign_texture_{i}.png"; Image.fromarray(arr).save(path)
            add(path,"image","benign","synthetic_seed=20261114")
        for i in range(4):
            arr=np.zeros((256,256,3),dtype=np.uint8); arr[:]=((i*31)%256,(i*67)%256,(i*97)%256)
            arr[::8,:,:]=rng.integers(0,256,size=arr[::8,:,:].shape,dtype=np.uint8)
            path=d/f"benign_graphic_{i}.png"; Image.fromarray(arr).save(path)
            add(path,"image","benign","synthetic_seed=20261114")
        add(args.blue3,"image","stego","official_ctf_artifact")
        with Image.open(args.blue3) as source:
            carrier=source.convert("RGB")
        for i,factor in enumerate((0.98,1.02,0.95,1.05)):
            variant=Image.fromarray(np.clip(np.asarray(carrier,dtype=np.float64)*factor,0,255).astype(np.uint8))
            path=d/f"stego_blue3_brightness_{i}.png";variant.save(path)
            add(path,"image","stego","derived_from_official_stego")
        sr=44100; duration=7.0; n=int(sr*duration); t=np.arange(n)/sr
        for i in range(8):
            noise=rng.normal(0,0.04,n)
            path=d/f"benign_audio_{i}.wav"
            sf.write(path,np.column_stack([noise,noise*0.9]),sr)
            add(path,"audio","benign","synthetic_seed=20261114")
        add(args.sleepy,"audio","stego","official_ctf_artifact")
        source_audio,source_sr=sf.read(args.sleepy,always_2d=True,dtype="float64")
        for i,gain in enumerate((0.8,0.9,1.1,1.2)):
            path=d/f"stego_sleepy_gain_{i}.wav"
            sf.write(path,source_audio*gain,source_sr)
            add(path,"audio","stego","derived_from_official_stego")
        # Compare both extraction modes on identical target bytes.
        trials={}
        for label,reference_path in (("reference_free",None),("reference_assisted",args.reference)):
            try:
                result=solve_sleepy(args.sleepy,reference=reference_path,expected_text=args.expected)
                trials[label]={"status":"completed","reference_used":reference_path is not None,
                  "format_valid":result["format_valid"],"ground_truth_match":result["ground_truth_match"],
                  "success":result["success"],"decoded_length":result["decoded_length"],
                  "symbol_count":result["measured_symbol_count"],
                  "separator_count":result["symbol_counts"]["separator"],
                  "errors":result["errors"],"decoded_text":result["decoded_text"]}
            except Exception as exc:
                trials[label]={"status":"failed","reference_used":reference_path is not None,
                  "error_type":type(exc).__name__,"error":str(exc)}
        trial_result={"expected_text_used_only_for_validation":True,"trials":trials,
          "note":"Reference-free and reference-assisted results are kept separate; expected text is used only for exact-match validation, never extraction."}
        with (args.out/"reference_comparison.json").open("w",encoding="utf-8") as f:
            json.dump(trial_result,f,indent=2,ensure_ascii=False)
    summaries={}
    for kind in ("image","audio"):
        subset=[r for r in rows if r["kind"]==kind]
        summaries[kind]={**confusion(subset),"sample_count":len(subset),
                         "benign_count":sum(r["label"]=="benign" for r in subset),
                         "stego_count":sum(r["label"]=="stego" for r in subset)}
    with (args.out/"benchmark.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    result={"dataset_note":"Only two positive official challenge artifacts; benign controls are deterministic synthetic samples, not a representative real-world corpus.",
            "seed":20261114,"thresholds":"fixed heuristics in src/steganalysis.py; not learned or calibrated",
            "metrics":summaries,"reference_comparison":"reference_comparison.json",
            "csv":"benchmark.csv"}
    (args.out/"benchmark.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=="__main__": main()
