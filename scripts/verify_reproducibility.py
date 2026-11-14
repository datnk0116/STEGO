#!/usr/bin/env python3
"""Run the local evidence gate for official artifacts and regression tests.

This gate does not run GitHub Actions, rebuild DOCX/PDF/ZIP, tune detector
thresholds, or claim that exploratory robustness results generalize.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from solve_challenges import solve_blue, solve_sleepy  # noqa: E402

BLUE_FLAG = "byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}"
SLEEPY_FLAG = "ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}"

ARTIFACTS = {
    "blue3": {
        "path": "data/blue3/blue.png",
        "bytes": 9406,
        "sha256": "009dab85bf6ccc5b42b8efa5f959ab6efa0c556b37eb6b4a77a21ec3356b721e",
    },
    "sleepy_alarm": {
        "path": "data/sleepy_alarm/morning_n_breakfast.mp3",
        "bytes": 179283,
        "sha256": "bd181876c2d28152b9c3982fd88945d4e681fd93d49477622ea5841a3ff25ae2",
    },
    "sleepy_alarm_reference": {
        "path": "data/sleepy_alarm/morning_n_breakfast_original.mp3",
        "bytes": 160495,
        "sha256": "d0c283834955e54d68b0bba723ccd194142a428d2de74722e5f1dff3ccbd94ad",
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_value(*args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        )
        return completed.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _check_artifacts() -> dict:
    results = {}
    for name, expected in ARTIFACTS.items():
        path = ROOT / expected["path"]
        if not path.is_file():
            results[name] = {
                **expected,
                "exists": False,
                "passed": False,
                "actual_bytes": None,
                "actual_sha256": None,
            }
            continue
        actual_bytes = path.stat().st_size
        actual_hash = _sha256(path)
        results[name] = {
            **expected,
            "exists": True,
            "actual_bytes": actual_bytes,
            "actual_sha256": actual_hash,
            "passed": (
                actual_bytes == expected["bytes"]
                and actual_hash == expected["sha256"]
            ),
        }
    return results


def _run_unit_tests(log_path: Path) -> dict:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    completed = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, check=False
    )
    output = completed.stdout + completed.stderr
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(output, encoding="utf-8")
    match = re.search(r"Ran\s+(\d+)\s+tests?", output)
    return {
        "command": "python -m unittest discover -s tests -v",
        "exit_code": completed.returncode,
        "tests_run": int(match.group(1)) if match else None,
        "passed": completed.returncode == 0 and match is not None,
        "log": log_path.relative_to(ROOT).as_posix(),
        "tail": output[-2500:],
    }


def _run_official_decoders() -> dict:
    blue_path = ROOT / ARTIFACTS["blue3"]["path"]
    sleepy_path = ROOT / ARTIFACTS["sleepy_alarm"]["path"]
    reference_path = ROOT / ARTIFACTS["sleepy_alarm_reference"]["path"]
    outcome = {}

    try:
        candidate, attempts = solve_blue(blue_path)
        outcome["blue3"] = {
            "candidate": candidate,
            "expected_length": len(BLUE_FLAG),
            "attempt_count": len(attempts),
            "exact_match": candidate == BLUE_FLAG,
            "passed": candidate == BLUE_FLAG,
        }
    except Exception as exc:  # retain the exception in the evidence report
        outcome["blue3"] = {
            "passed": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    try:
        result = solve_sleepy(
            sleepy_path, reference=reference_path, expected_text=SLEEPY_FLAG
        )
        outcome["sleepy_alarm_reference_assisted"] = {
            "passed": bool(
                result["success"]
                and result["ground_truth_match"]
                and result["measured_symbol_count"] == 350
                and result["symbol_counts"]["separator"] == 38
                and result["decoded_length"] == 39
            ),
            "exact_match": result["ground_truth_match"],
            "format_valid": result["format_valid"],
            "symbol_count": result["measured_symbol_count"],
            "separator_count": result["symbol_counts"]["separator"],
            "byte_count": result["byte_count"],
            "byte_errors": result["errors"],
            "alignment_lag_samples": result["reference_alignment"]["alignment_lag_samples"],
            "alignment_correlation": result["reference_alignment"]["normalized_abs_correlation"],
            "cluster_centers": result["amplitude_cluster_centers"],
        }
    except Exception as exc:
        outcome["sleepy_alarm_reference_assisted"] = {
            "passed": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    # This is a measurement of the current limitation, not a gate failure.
    # It records whether blind/reference-free extraction currently succeeds.
    try:
        result = solve_sleepy(sleepy_path, expected_text=SLEEPY_FLAG)
        outcome["sleepy_alarm_reference_free"] = {
            "currently_exact": bool(result["success"]),
            "format_valid": result["format_valid"],
            "decoded_length": result["decoded_length"],
            "symbol_count": result["measured_symbol_count"],
            "separator_count": result["symbol_counts"]["separator"],
            "byte_errors": result["errors"],
        }
    except Exception as exc:
        outcome["sleepy_alarm_reference_free"] = {
            "currently_exact": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    return outcome


def main() -> int:
    results_dir = ROOT / "results" / "verification"
    logs_dir = ROOT / "results" / "logs"
    results_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    tests = _run_unit_tests(logs_dir / "quality-gate-tests.log")
    artifacts = _check_artifacts()
    decoders = _run_official_decoders()

    packages = {}
    for package in (
        "Pillow", "numpy", "scipy", "matplotlib", "soundfile", "python-docx"
    ):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None

    decoder_passed = all(
        decoders.get(name, {}).get("passed", False)
        for name in ("blue3", "sleepy_alarm_reference_assisted")
    )
    overall = (
        tests["passed"]
        and all(item["passed"] for item in artifacts.values())
        and decoder_passed
    )

    report = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": {
            "commit": _git_value("rev-parse", "HEAD"),
            "branch": _git_value("branch", "--show-current"),
            "status_short": _git_value("status", "--short"),
        },
        "environment": {
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "python": sys.version,
            "packages": packages,
        },
        "unit_tests": tests,
        "artifact_integrity": artifacts,
        "official_decoder_verification": decoders,
        "overall_passed": overall,
        "scope_note": (
            "A local reproducibility gate for pinned artifacts and tests. "
            "It does not certify population-level robustness or general steganalysis."
        ),
    }
    output_path = results_dir / "quality-gate.json"
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "overall_passed": overall,
        "tests_run": tests["tests_run"],
        "unit_tests_passed": tests["passed"],
        "artifact_integrity_passed": all(x["passed"] for x in artifacts.values()),
        "blue3_exact_match": decoders.get("blue3", {}).get("exact_match", False),
        "sleepy_alarm_exact_match": decoders.get(
            "sleepy_alarm_reference_assisted", {}
        ).get("exact_match", False),
        "quality_gate_json": output_path.relative_to(ROOT).as_posix(),
        "unit_test_log": tests["log"],
    }, indent=2, ensure_ascii=False))
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
