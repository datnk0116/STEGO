#!/usr/bin/env python3
"""Execute and compare the local Blue 3 solver with the pinned BYUCTF solver.

The original upstream solve.py is fetched at an immutable commit and run
against the same input bytes in a temporary working directory. No speed
comparison is made.
"""
from __future__ import annotations

from datetime import datetime, timezone
import argparse
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, __version__ as pillow_version

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from solve_challenges import solve_blue

UPSTREAM = {
    "repository": "https://github.com/BYU-CSA/old-ctf-challenges",
    "path": "forensics-steganography/blue-3/solve.py",
    "commit": "18c8f246756e79069c1cb1753c8bfea5e73e31f5",
    "raw_source_url": (
        "https://raw.githubusercontent.com/BYU-CSA/old-ctf-challenges/"
        "18c8f246756e79069c1cb1753c8bfea5e73e31f5/"
        "forensics-steganography/blue-3/solve.py"
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_upstream_source() -> str:
    """Download the exact raw solve.py at the immutable upstream commit."""
    with urllib.request.urlopen(UPSTREAM["raw_source_url"], timeout=30) as response:
        source = response.read().decode("utf-8")
    if not source.strip():
        raise RuntimeError("upstream solve.py download returned an empty file")
    return source


def run_upstream_reference(image_path: Path, source_text: str):
    """Execute upstream solve.py in an isolated cwd with the same blue.png bytes."""
    with tempfile.TemporaryDirectory(prefix="blue3-upstream-") as temporary:
        working = Path(temporary)
        shutil.copy2(image_path, working / "blue.png")
        solver_path = working / "solve.py"
        solver_path.write_text(source_text, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(solver_path)],
            cwd=working, capture_output=True, text=True,
        )
    if result.returncode != 0:
        raise RuntimeError(
            f"upstream solver exited {result.returncode}: {result.stderr.strip()}"
        )
    output_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not output_lines:
        raise RuntimeError(
            "upstream solver produced no candidate; stderr=" + result.stderr.strip()
        )
    candidate = output_lines[-1]
    if not re.fullmatch(r"byuctf\{[0-9A-Za-z_]*\}", candidate):
        raise RuntimeError(f"upstream output is not a complete BYUCTF candidate: {candidate!r}")
    return candidate, result.stdout




def compare_solvers(image_path: Path, upstream_source: str | None = None) -> dict:
    image_path = Path(image_path)
    if not image_path.is_file():
        raise FileNotFoundError(image_path)
    with Image.open(image_path) as image:
        dimensions, image_format, image_mode = list(image.size), image.format, image.mode
    digest = sha256(image_path)

    source_text = upstream_source if upstream_source is not None else download_upstream_source()
    upstream_candidate, upstream_stdout = run_upstream_reference(image_path, source_text)
    upstream_source_sha256 = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    local_candidate, local_attempts = solve_blue(image_path)

    return {
        "status": "COMPLETED",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "upstream": UPSTREAM,
        "input": {
            "path": str(image_path), "sha256": digest, "bytes": image_path.stat().st_size,
            "format": image_format, "mode": image_mode, "dimensions": dimensions,
        },
        "environment": {
            "python": platform.python_version(), "platform": platform.platform(),
            "pillow": pillow_version,
        },
        "comparison": {
            "upstream_candidate": upstream_candidate,
            "local_candidate": local_candidate,
            "upstream_candidate_length": len(upstream_candidate),
            "local_candidate_length": len(local_candidate) if local_candidate is not None else None,
            "upstream_source_sha256": upstream_source_sha256,
            "upstream_stdout": upstream_stdout,
            "local_attempts": len(local_attempts),
            "exact_candidate_match": upstream_candidate == local_candidate,
        },
        "interpretation": (
            "The original pinned upstream source file was executed in a temporary working directory. "
            "No speed comparison is claimed; local function and upstream subprocess have different launch overhead."
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, nargs="?", default=Path("data/blue3/blue.png"))
    parser.add_argument("--json-out", type=Path,
                        default=Path("results/blue3/reference_comparison/comparison.json"))
    parser.add_argument("--log-out", type=Path,
                        default=Path("results/blue3/reference_comparison/comparison.log"))
    args = parser.parse_args(argv)
    try:
        result = compare_solvers(args.image)
    except Exception as exc:
        result = {
            "status": "FAILED", "upstream": UPSTREAM, "input_path": str(args.image),
            "error_type": type(exc).__name__, "error": str(exc),
            "note": "No candidate or runtime is inferred when execution fails.",
        }
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                                  encoding="utf-8")
        args.log_out.write_text(
            f"COMMAND: python src/blue3/reference_comparison.py {args.image}\n"
            f"STATUS: FAILED\n{type(exc).__name__}: {exc}\n", encoding="utf-8"
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
    cmp = result["comparison"]
    args.log_out.write_text(
        f"COMMAND: python src/blue3/reference_comparison.py {args.image}\n"
        f"UPSTREAM COMMIT: {UPSTREAM['commit']}\n"
        f"INPUT SHA-256: {result['input']['sha256']}\n"
        f"UPSTREAM CANDIDATE: {cmp['upstream_candidate']!r}\n"
        f"LOCAL CANDIDATE: {cmp['local_candidate']!r}\n"
        f"EXACT CANDIDATE MATCH: {cmp['exact_candidate_match']}\n"
        f"UPSTREAM SOURCE SHA-256: {cmp['upstream_source_sha256']}\n"
        f"LOCAL ATTEMPTS: {cmp['local_attempts']}\n"
        "NOTE: Functional cross-check only; not a speed comparison.\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if cmp["exact_candidate_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
