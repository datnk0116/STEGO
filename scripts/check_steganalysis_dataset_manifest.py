#!/usr/bin/env python3
"""Validate file integrity and source-disjoint splits for an external stego corpus."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SPLITS = {"train", "validation", "test"}
LABELS = {"benign", "stego"}
REQUIRED_FIELDS = {
    "relative_path", "source_url", "license", "modality", "label", "carrier",
    "transformation", "host_source_id", "secret_source_id", "bh_parameter",
    "split", "bytes", "sha256",
}


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_manifest(root: Path, manifest_path: Path) -> dict:
    root = Path(root).resolve()
    manifest_path = Path(manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    errors: list[str] = []
    checks: dict[str, bool] = {}

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "passed": False, "errors": [f"cannot read manifest: {exc}"],
            "checks": {"manifest_readable": False}, "sample_count": 0,
        }
    if not isinstance(manifest, dict):
        return {
            "passed": False, "errors": ["manifest root must be a JSON object"],
            "checks": {"manifest_object": False}, "sample_count": 0,
        }

    checks["schema_version"] = manifest.get("schema_version") == 1
    if not checks["schema_version"]:
        errors.append("schema_version must equal 1")

    source = manifest.get("dataset_source")
    source_ok = (
        isinstance(source, dict)
        and isinstance(source.get("url"), str) and source["url"].startswith("https://")
        and isinstance(source.get("license"), str) and bool(source["license"].strip())
    )
    checks["dataset_source"] = source_ok
    if not source_ok:
        errors.append("dataset_source must contain an HTTPS url and a non-empty license")

    samples = manifest.get("samples")
    if not isinstance(samples, list) or not samples:
        checks["nonempty_samples"] = False
        errors.append("samples must be a non-empty list; discovery-only records are not sample manifests")
        samples = []
    else:
        checks["nonempty_samples"] = True

    seen_paths: set[str] = set()
    hash_splits: dict[str, set[str]] = {}
    source_splits = {"host_source_id": {}, "secret_source_id": {}}
    verified_files = 0

    for index, sample in enumerate(samples):
        label = f"sample[{index}]"
        if not isinstance(sample, dict):
            errors.append(f"{label} must be an object")
            continue

        missing = sorted(REQUIRED_FIELDS - sample.keys())
        if missing:
            errors.append(f"{label} missing fields: {missing}")
            continue

        relative = sample.get("relative_path")
        if not isinstance(relative, str) or not relative:
            errors.append(f"{label}.relative_path must be a non-empty relative path")
            continue
        rel_path = Path(relative)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            errors.append(f"{label}.relative_path must not escape the dataset root: {relative}")
            continue
        normalized = rel_path.as_posix()
        if normalized in seen_paths:
            errors.append(f"duplicate relative_path: {normalized}")
            continue
        seen_paths.add(normalized)

        file_path = (root / rel_path).resolve()
        if root not in file_path.parents:
            errors.append(f"{label}.relative_path resolves outside the dataset root")
            continue
        if not file_path.is_file():
            errors.append(f"missing sample file: {normalized}")
            continue

        expected_bytes = sample.get("bytes")
        expected_hash = sample.get("sha256")
        if not isinstance(expected_bytes, int) or expected_bytes < 0:
            errors.append(f"{label}.bytes must be a non-negative integer")
            continue
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            errors.append(f"{label}.sha256 must be a lowercase SHA-256 hex digest")
            continue

        actual_bytes = file_path.stat().st_size
        actual_hash = digest_file(file_path)
        file_ok = actual_bytes == expected_bytes and actual_hash == expected_hash
        if not file_ok:
            errors.append(
                f"integrity mismatch for {normalized}: "
                f"expected {expected_bytes} bytes/{expected_hash}, "
                f"actual {actual_bytes} bytes/{actual_hash}"
            )
        else:
            verified_files += 1

        split = sample.get("split")
        if split not in SPLITS:
            errors.append(f"{label}.split must be one of {sorted(SPLITS)}")
            continue
        if sample.get("label") not in LABELS:
            errors.append(f"{label}.label must be one of {sorted(LABELS)}")
        for field in ("source_url", "license", "modality", "carrier", "transformation"):
            value = sample.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label}.{field} must be a non-empty string")

        for source_field, mapping in source_splits.items():
            source_id = sample.get(source_field)
            if source_id is None or source_id == "":
                continue
            if not isinstance(source_id, str):
                errors.append(f"{label}.{source_field} must be a string or null")
                continue
            mapping.setdefault(source_id, set()).add(split)

        hash_splits.setdefault(actual_hash, set()).add(split)

    leakage = []
    for field, mapping in source_splits.items():
        for source_id, split_values in mapping.items():
            if len(split_values) > 1:
                leakage.append(f"{field}={source_id} appears in splits {sorted(split_values)}")
    for sample_hash, split_values in hash_splits.items():
        if len(split_values) > 1:
            leakage.append(f"SHA-256 {sample_hash} appears in splits {sorted(split_values)}")
    checks["source_split_disjointness"] = not leakage
    if leakage:
        errors.extend("split leakage: " + item for item in leakage)

    checks["file_integrity"] = verified_files == len(samples) and bool(samples)
    if not checks["file_integrity"] and samples:
        errors.append(f"only {verified_files}/{len(samples)} sample files passed size/SHA-256")

    return {
        "passed": not errors,
        "errors": errors,
        "checks": checks,
        "sample_count": len(samples),
        "verified_files": verified_files,
        "source_split_counts": {
            field: {source_id: sorted(split_values) for source_id, split_values in mapping.items()}
            for field, mapping in source_splits.items()
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    result = validate_manifest(args.root, args.manifest)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
