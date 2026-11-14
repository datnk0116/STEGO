#!/usr/bin/env python3
"""Generate publication-ready Blue 3 diagnostic figures from the original PNG."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image",type=Path)
    parser.add_argument("--length",type=int,default=50,
                        help="candidate flag length; the recovered Blue 3 flag has 50 characters")
    parser.add_argument("--base-color",type=int,nargs=3,default=(64,77,205),
                        metavar=("R","G","B"))
    parser.add_argument("--out-dir",type=Path,default=Path("results/blue3/figures"))
    args=parser.parse_args()
    if not args.image.is_file():
        parser.error(f"image does not exist: {args.image}")
    if args.length < 2 or args.length > min(Image.open(args.image).size):
        parser.error("length is outside the supported range")
    with Image.open(args.image) as im:
        rgb=np.asarray(im.convert("RGB"),dtype=np.int16)
    base=np.asarray(args.base_color,dtype=np.int16)
    delta=rgb-base
    # Only positive increments are meaningful in the generator; preserve
    # signed deltas in the reported diagnostic in case an input is altered.
    signed_sum=delta.sum(axis=2)
    magnitude=np.max(np.abs(delta),axis=2)
    cell_w=rgb.shape[1]//args.length
    cell_h=rgb.shape[0]//args.length
    contributions=[]
    for i in range(args.length):
        region=signed_sum[i*cell_h:(i+1)*cell_h,
                           i*cell_w:(i+1)*cell_w]
        contributions.append(int(region.sum()))
    args.out_dir.mkdir(parents=True,exist_ok=True)

    fig,axes=plt.subplots(1,3,figsize=(15,4.6))
    for c,name in enumerate(("R","G","B")):
        axes[0].hist(rgb[:,:,c].ravel(),bins=np.arange(-0.5,256.5,1),
                     histtype="step",label=name)
    axes[0].set_xlim(max(0,int(base.min())-2),min(255,int(base.max())+8))
    axes[0].set_title("Channel-value distributions")
    axes[0].set_xlabel("8-bit channel value"); axes[0].set_ylabel("Pixel count")
    axes[0].legend()

    im=axes[1].imshow(magnitude,cmap="magma",interpolation="nearest")
    axes[1].set_title("Maximum absolute RGB delta")
    axes[1].set_xlabel("x (pixel)"); axes[1].set_ylabel("y (pixel)")
    fig.colorbar(im,ax=axes[1],fraction=0.046,pad=0.04)
    axes[1].set_xticks(np.arange(0,rgb.shape[1]+1,cell_w))
    axes[1].set_yticks(np.arange(0,rgb.shape[0]+1,cell_h))
    axes[1].grid(color="cyan",linewidth=0.25,alpha=0.7)

    axes[2].bar(np.arange(args.length),contributions,width=0.85)
    axes[2].set_title("Diagonal-region RGB delta sums")
    axes[2].set_xlabel("Character-region index"); axes[2].set_ylabel("Summed delta")
    axes[2].axhline(0,linewidth=0.7)
    fig.suptitle("Blue 3 — image steganalysis diagnostics",fontsize=14)
    fig.tight_layout()
    figure_path=args.out_dir/"blue3_diagnostics.png"
    fig.savefig(figure_path,dpi=180,bbox_inches="tight")
    plt.close(fig)

    result={
        "image":str(args.image),
        "base_color_rgb":[int(v) for v in base],
        "candidate_length":args.length,
        "region_width":cell_w,
        "region_height":cell_h,
        "covered_diagonal_region_pixels":args.length*cell_w*cell_h,
        "unused_right_margin_pixels":int(rgb.shape[1]-args.length*cell_w),
        "unused_bottom_margin_pixels":int(rgb.shape[0]-args.length*cell_h),
        "region_delta_sums":contributions,
        "figure":str(figure_path),
    }
    print(json.dumps(result,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
