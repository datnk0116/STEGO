#!/usr/bin/env python3
"""Validate submission artifacts, hashes, PDF layout and build-input freshness."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

MANIFEST = Path("results/submission/package-manifest.json")
ARTIFACT_PATHS = {
    "docx": "results/submission/STUDENT_UETCN3124_CTF_Report.docx",
    "pdf": "results/submission/STUDENT_UETCN3124_CTF_Report.pdf",
    "zip": "results/submission/STUDENT_UETCN3124_Scripts.zip",
}
ALLOWED_POST_BUILD_PATHS = set(ARTIFACT_PATHS.values()) | {
    str(MANIFEST), "results/submission/pdf-metadata.txt",
    "results/submission/reference.docx",
}
REQUIRED_ZIP_FILES = {"README.md", "requirements.txt", "report/REPORT.md"}
REQUIRED_ZIP_PREFIXES = (
    "data/", "src/", "tests/", "scripts/", "references/", "docs/", "results/"
)
FORBIDDEN_PARTS = {".git", ".venv", "venv", "__pycache__"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".tmp", ".bak", ".zip", ".docx", ".pdf"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_check(root: Path, path: Path, max_main_pages: int):
    result = subprocess.run(
        [sys.executable, str(root / "scripts/check_report_pdf.py"),
         str(path), "--max-main-pages", str(max_main_pages)],
        cwd=root, capture_output=True, text=True,
    )
    output = (result.stdout + "\n" + result.stderr).strip()
    total_match = re.search(r"^PDF total pages:\s*(\d+)", output, re.M)
    body_match = re.search(r"^Main-body pages .*:\s*(\d+)", output, re.M)
    total = int(total_match.group(1)) if total_match else None
    body = int(body_match.group(1)) if body_match else None
    return result.returncode == 0 and total is not None and body is not None, total, body, output


def inspect_docx(path: Path) -> tuple[bool, str]:
    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            names = set(archive.namelist())
        required = {"[Content_Types].xml", "word/document.xml"}
        if bad_member:
            return False, f"corrupt DOCX member: {bad_member}"
        if not required.issubset(names):
            return False, f"DOCX is missing OOXML members: {sorted(required - names)}"
        return True, "DOCX OOXML container is readable"
    except (OSError, zipfile.BadZipFile) as exc:
        return False, f"cannot inspect DOCX: {exc}"


def inspect_zip(path: Path):
    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            names = [name for name in archive.namelist() if not name.endswith("/")]
        missing_files = sorted(REQUIRED_ZIP_FILES - set(names))
        missing_prefixes = [
            prefix for prefix in REQUIRED_ZIP_PREFIXES
            if not any(name.startswith(prefix) for name in names)
        ]
        forbidden = [
            name for name in names
            if any(part in FORBIDDEN_PARTS for part in Path(name).parts)
            or Path(name).suffix.lower() in FORBIDDEN_SUFFIXES
            or name in {".DS_Store", ".env"}
        ]
        details = []
        if bad_member:
            details.append(f"corrupt member: {bad_member}")
        if missing_files:
            details.append(f"missing required files: {missing_files}")
        if missing_prefixes:
            details.append(f"missing required directories: {missing_prefixes}")
        if forbidden:
            details.append(f"forbidden entries: {forbidden[:20]}")
        return bad_member is None, not (missing_files or missing_prefixes or forbidden), details
    except (OSError, zipfile.BadZipFile) as exc:
        return False, False, [f"cannot inspect ZIP: {exc}"]


def validate_submission_manifest(root: Path, *, allow_pending_visual: bool = False) -> dict:
    root = Path(root).resolve()
    errors = []
    derived = {
        "freshness": "NOT_VERIFIED",
        "build_input_commit": None,
        "changed_after_build": [],
        "uncommitted_unexpected_paths": [],
    }
    manifest_path = root / MANIFEST
    if not manifest_path.is_file():
        return {"passed": False, "errors": ["package manifest is missing"], "derived": derived}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"passed": False, "errors": [f"invalid package manifest: {exc}"], "derived": derived}
    if not isinstance(manifest, dict):
        return {"passed": False, "errors": ["package manifest must be a JSON object"], "derived": derived}

    if manifest.get("status") == "NOT_BUILT":
        return {
            "passed": False,
            "errors": ["submission package has not been rebuilt from the current source revision"],
            "derived": derived,
            "manifest": manifest,
        }

    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    built_at = manifest.get("built_at_utc")
    try:
        parsed_built_at = datetime.fromisoformat(built_at.replace("Z", "+00:00"))
        built_at_valid = (
            parsed_built_at.tzinfo is not None
            and parsed_built_at.utcoffset() == timezone.utc.utcoffset(parsed_built_at)
        )
    except (AttributeError, TypeError, ValueError):
        built_at_valid = False
    if not built_at_valid:
        errors.append("built_at_utc must be a valid timezone-aware ISO-8601 timestamp")
    build_command = manifest.get("build_command")
    if not isinstance(build_command, list) or not build_command or any(
        not isinstance(part, str) or not part.strip() for part in build_command
    ):
        errors.append("build_command must be a non-empty string array")
    required_tools = {
        "python", "platform", "pandoc", "libreoffice", "pdfinfo",
        "pdftotext", "unzip", "python-docx",
    }
    versions = manifest.get("tool_versions")
    missing_tools = sorted(required_tools - set(versions)) if isinstance(versions, dict) else sorted(required_tools)
    invalid_versions = (
        not isinstance(versions, dict)
        or any(not isinstance(value, str) or not value.strip() for value in versions.values())
    )
    if missing_tools or invalid_versions:
        errors.append(f"tool_versions incomplete; missing={missing_tools}")

    build_commit = manifest.get("build_input_commit")
    derived["build_input_commit"] = build_commit
    valid_sha = isinstance(build_commit, str) and re.fullmatch(r"[0-9a-f]{40}", build_commit)
    if not valid_sha:
        errors.append("build_input_commit must be a full 40-character commit SHA")
    else:
        exists = subprocess.run(
            ["git", "cat-file", "-e", f"{build_commit}^{{commit}}"],
            cwd=root, capture_output=True,
        ).returncode == 0
        if not exists:
            errors.append("build_input_commit does not exist in this repository")
        else:
            ancestor = subprocess.run(
                ["git", "merge-base", "--is-ancestor", build_commit, "HEAD"],
                cwd=root, capture_output=True,
            ).returncode == 0
            if not ancestor:
                errors.append("build_input_commit is not an ancestor of current HEAD")
            else:
                changed = subprocess.run(
                    ["git", "diff", "--name-only", f"{build_commit}..HEAD"],
                    cwd=root, capture_output=True, text=True, check=True,
                ).stdout.splitlines()
                derived["changed_after_build"] = changed
                unexpected = sorted(set(changed) - ALLOWED_POST_BUILD_PATHS)
                if unexpected:
                    errors.append(
                        "build inputs changed after build_input_commit: " + ", ".join(unexpected)
                    )

    status_result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root, capture_output=True, text=True,
    )
    if status_result.returncode != 0:
        errors.append("cannot inspect working tree status")
    else:
        dirty_paths = []
        for line in status_result.stdout.splitlines():
            if len(line) > 3:
                dirty_path = line[3:].strip().strip('"')
                dirty_paths.append(dirty_path.split(" -> ", 1)[-1])
        unexpected_dirty = sorted(set(dirty_paths) - ALLOWED_POST_BUILD_PATHS)
        derived["uncommitted_unexpected_paths"] = unexpected_dirty
        if unexpected_dirty:
            errors.append(
                "uncommitted package input changes or temporary files: "
                + ", ".join(unexpected_dirty)
            )

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append("artifacts must be an object")
        artifacts = {}
    for key, expected_path in ARTIFACT_PATHS.items():
        item = artifacts.get(key)
        if not isinstance(item, dict):
            errors.append(f"artifact record missing: {key}")
            continue
        if item.get("path") != expected_path:
            errors.append(f"{key}.path must be {expected_path}")
            continue
        path = root / expected_path
        if not path.is_file():
            errors.append(f"artifact missing: {expected_path}")
            continue
        if item.get("bytes") != path.stat().st_size:
            errors.append(f"byte-size mismatch: {expected_path}")
        if item.get("sha256") != sha256(path):
            errors.append(f"SHA-256 mismatch: {expected_path}")
        if key == "docx":
            docx_ok, docx_detail = inspect_docx(path)
            derived["docx_integrity"] = "PASS" if docx_ok else "FAIL"
            if not docx_ok:
                errors.append("DOCX integrity check failed: " + docx_detail)
        if key == "pdf":
            if not isinstance(item.get("page_count"), int) or item["page_count"] < 1:
                errors.append("PDF page_count must be a positive integer")
            limit = int(manifest.get("max_main_pages", 17))
            ok, total, body, detail = pdf_check(root, path, limit)
            if not ok:
                errors.append("PDF page checker failed: " + detail.replace("\n", " | "))
            elif item.get("page_count") != total:
                errors.append(f"PDF page count mismatch: manifest={item.get('page_count')}, actual={total}")
            if body is not None:
                derived["actual_main_body_pages"] = body
        elif item.get("page_count") is not None:
            errors.append(f"{key}.page_count must be null")

    zip_path = root / ARTIFACT_PATHS["zip"]
    if zip_path.is_file():
        zip_integrity, zip_contents, details = inspect_zip(zip_path)
        derived["zip_integrity"] = "PASS" if zip_integrity else "FAIL"
        derived["zip_contents"] = "PASS" if zip_contents else "FAIL"
        if not zip_integrity:
            errors.append("ZIP integrity check failed")
        if not zip_contents:
            errors.append("ZIP content inspection failed: " + "; ".join(details))

    checks = manifest.get("checks")
    if not isinstance(checks, dict):
        errors.append("checks must be an object")
        checks = {}
    for name in ("docx_integrity", "pdf_page_check", "zip_integrity", "zip_contents"):
        if checks.get(name) != "PASS":
            errors.append(f"manifest check is not PASS: {name}")
    visual = checks.get("pdf_visual_inspection")
    if visual != "PASS" and not allow_pending_visual:
        errors.append("PDF visual inspection has not been explicitly confirmed")
    if visual == "PASS":
        confirmation = manifest.get("pdf_visual_inspection_confirmed_at_utc")
        try:
            parsed_confirmation = datetime.fromisoformat(confirmation.replace("Z", "+00:00"))
            confirmation_valid = (
                parsed_confirmation.tzinfo is not None
                and parsed_confirmation.utcoffset() == timezone.utc.utcoffset(parsed_confirmation)
            )
        except (AttributeError, TypeError, ValueError):
            confirmation_valid = False
        if not confirmation_valid:
            errors.append("PDF visual inspection PASS requires a timezone-aware confirmation timestamp")
    verified = manifest.get("status") == "VERIFIED"
    if not verified and not allow_pending_visual:
        errors.append("manifest status is not VERIFIED")

    hard_mismatch = any(
        any(token in error for token in (
            "mismatch", "missing", "failed", "changed after", "not an ancestor",
            "does not exist", "invalid", "must be full", "uncommitted",
        ))
        for error in errors
    )
    if hard_mismatch:
        derived["freshness"] = "STALE"
    elif verified and visual == "PASS" and not errors:
        derived["freshness"] = "FRESH"
    else:
        derived["freshness"] = "NOT_VERIFIED"
    return {
        "passed": not errors and derived["freshness"] == "FRESH",
        "errors": errors, "derived": derived, "manifest": manifest,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--confirm-pdf-visual-inspection", action="store_true",
                        help="Record the user's visual inspection of the final PDF.")
    parser.add_argument("--require-verified", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    path = root / MANIFEST

    if args.confirm_pdf_visual_inspection:
        if not path.is_file():
            parser.error(f"manifest not found: {path}")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest.setdefault("checks", {})["pdf_visual_inspection"] = "PASS"
        manifest["pdf_visual_inspection_confirmed_at_utc"] = datetime.now(timezone.utc).isoformat()
        manifest["status"] = "NOT_VERIFIED"
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        preliminary = validate_submission_manifest(root, allow_pending_visual=True)
        if preliminary["errors"]:
            for error in preliminary["errors"]:
                print(f"[FAIL] {error}")
            return 1
        manifest["status"] = "VERIFIED"
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report = validate_submission_manifest(root)
    print("SUBMISSION PACKAGE VALIDATION")
    for error in report["errors"]:
        print(f"[FAIL] {error}")
    if report["passed"]:
        print("[PASS] All manifest, hash, PDF and ZIP checks passed.")
    else:
        print(f"[WARN] package status: {report['derived']['freshness']}")
    print(json.dumps(report["derived"], indent=2, ensure_ascii=False))
    if args.require_verified and not report["passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
