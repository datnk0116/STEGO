#!/usr/bin/env python3
"""Build DOCX, PDF and source ZIP locally; this script does not invoke GitHub Actions."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "submission"
DOCX = OUT / "STUDENT_UETCN3124_CTF_Report.docx"
PDF = OUT / "STUDENT_UETCN3124_CTF_Report.pdf"
ZIP = OUT / "STUDENT_UETCN3124_Scripts.zip"
MANIFEST = OUT / "package-manifest.json"

TOP_FILES = [".gitignore", "README.md", "requirements.txt"]
DIRECTORIES = [".github", "data", "src", "tests", "scripts", "references", "report", "results", "docs"]
EXCLUDED_PARTS = {".venv", "venv", "__pycache__", ".git"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp", ".bak", ".zip"}
REQUIRED_ZIP_FILES = {"README.md", "requirements.txt", "report/REPORT.md"}
REQUIRED_ZIP_PREFIXES = ("data/", "src/", "tests/", "scripts/", "references/", "docs/", "results/")


def run(command):
    print("+", " ".join(map(str, command)), flush=True)
    return subprocess.run(command, cwd=ROOT, check=True, text=True)


def require_tools(names):
    missing = [name for name in names if shutil.which(name) is None]
    if missing:
        raise SystemExit("Missing tools: " + ", ".join(missing)
                         + ". Install Pandoc, LibreOffice, Poppler and unzip before building.")


def git_output(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout.strip()


def tool_version(name, args):
    result = subprocess.run([name, *args], cwd=ROOT, capture_output=True, text=True)
    output = (result.stdout + "\n" + result.stderr).strip()
    return output.splitlines()[0] if result.returncode == 0 and output else "unavailable"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_zip():
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=8) as archive:
        for name in TOP_FILES:
            path = ROOT / name
            if path.is_file():
                archive.write(path, path.relative_to(ROOT).as_posix())
        for dirname in DIRECTORIES:
            folder = ROOT / dirname
            if not folder.exists():
                continue
            for path in sorted(folder.rglob("*")):
                if not path.is_file():
                    continue
                rel = path.relative_to(ROOT)
                if any(part in EXCLUDED_PARTS for part in rel.parts):
                    continue
                if path.suffix.lower() in EXCLUDED_SUFFIXES:
                    continue
                if rel.parts[:2] == ("results", "submission"):
                    continue
                if path.name in {".DS_Store", ".env"}:
                    continue
                archive.write(path, rel.as_posix())

    with zipfile.ZipFile(ZIP) as archive:
        bad_member = archive.testzip()
        names = [name for name in archive.namelist() if not name.endswith("/")]
    missing_files = REQUIRED_ZIP_FILES - set(names)
    missing_prefixes = [prefix for prefix in REQUIRED_ZIP_PREFIXES
                        if not any(name.startswith(prefix) for name in names)]
    forbidden = [name for name in names
                 if any(part in EXCLUDED_PARTS for part in Path(name).parts)
                 or Path(name).suffix.lower() in EXCLUDED_SUFFIXES | {".docx", ".pdf"}
                 or name in {".DS_Store", ".env"}]
    if bad_member or missing_files or missing_prefixes or forbidden:
        raise SystemExit(
            f"ZIP inspection failed: bad_member={bad_member}, missing_files={sorted(missing_files)}, "
            f"missing_dirs={missing_prefixes}, forbidden={forbidden[:20]}"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-main-pages", type=int, default=20,
                        help="Local ceiling. The course brief phrases 15 pages as a recommendation.")
    args = parser.parse_args()
    require_tools(["pandoc", "libreoffice", "pdfinfo", "pdftotext", "unzip"])

    dirty = git_output("status", "--porcelain", "--untracked-files=all")
    if dirty:
        raise SystemExit("Refusing to build from a dirty working tree. Commit input changes first.")
    build_input_commit = git_output("rev-parse", "HEAD")

    OUT.mkdir(parents=True, exist_ok=True)
    reference = OUT / "reference.docx"
    raw = OUT / "report-pandoc.docx"
    fixed = OUT / "report-fixed.docx"
    profile = Path("/tmp/lo-profile-stego-build")
    profile.mkdir(parents=True, exist_ok=True)

    run([sys.executable, str(ROOT / "scripts/create_reference_docx.py"), "--out", str(reference)])
    run(["pandoc", str(ROOT / "report/REPORT.md"),
         "--from=markdown+tex_math_dollars+pipe_tables", "--resource-path=.:report",
         "--standalone", f"--reference-doc={reference}",
         "--metadata", "lang=vi-VN",
         "--metadata", "title=Phân tích và đánh giá kỹ thuật Steganography",
         "--metadata", "author=Sinh viên UET.CN3124",
         "--output", str(raw)])
    run([sys.executable, str(ROOT / "scripts/fix_report_docx.py"), str(raw), "--out", str(fixed)])
    shutil.copy2(fixed, DOCX)
    with zipfile.ZipFile(DOCX) as docx_archive:
        bad_member = docx_archive.testzip()
        docx_members = set(docx_archive.namelist())
    if bad_member or not {"[Content_Types].xml", "word/document.xml"}.issubset(docx_members):
        raise SystemExit(f"DOCX OOXML integrity check failed: bad_member={bad_member}")
    PDF.unlink(missing_ok=True)
    run(["libreoffice", f"-env:UserInstallation=file://{profile}", "--headless",
         "--convert-to", "pdf", "--outdir", str(OUT), str(DOCX)])

    check = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_report_pdf.py"),
         str(PDF), "--max-main-pages", str(args.max_main_pages)],
        cwd=ROOT, check=True, capture_output=True, text=True)
    print(check.stdout, end="")
    info = subprocess.run(["pdfinfo", str(PDF)], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout
    (OUT / "pdf-metadata.txt").write_text(info, encoding="utf-8")
    pages_match = re.search(r"^Pages:\s+(\d+)", info, re.M)
    body_match = re.search(r"^Main-body pages .*:\s*(\d+)", check.stdout, re.M)
    if not pages_match or not body_match:
        raise SystemExit("PDF page metadata/checker output is incomplete")
    page_count = int(pages_match.group(1))
    main_body_pages = int(body_match.group(1))

    build_zip()
    unzip_result = subprocess.run(["unzip", "-t", str(ZIP)], cwd=ROOT,
                                  check=True, capture_output=True, text=True)
    print(unzip_result.stdout, end="")

    try:
        docx_version = version("python-docx")
    except PackageNotFoundError:
        docx_version = "not-installed"
    versions = {
        "python": sys.version.splitlines()[0],
        "platform": platform.platform(),
        "pandoc": tool_version("pandoc", ["--version"]),
        "libreoffice": tool_version("libreoffice", ["--version"]),
        "pdfinfo": tool_version("pdfinfo", ["-v"]),
        "pdftotext": tool_version("pdftotext", ["-v"]),
        "unzip": tool_version("unzip", ["-v"]),
        "python-docx": docx_version,
    }
    artifacts = {
        "docx": {"path": DOCX.relative_to(ROOT).as_posix(), "bytes": DOCX.stat().st_size,
                 "sha256": sha256(DOCX), "page_count": None,
                 "page_count_note": "Pagination belongs to the rendered PDF."},
        "pdf": {"path": PDF.relative_to(ROOT).as_posix(), "bytes": PDF.stat().st_size,
                "sha256": sha256(PDF), "page_count": page_count,
                "main_body_pages": main_body_pages},
        "zip": {"path": ZIP.relative_to(ROOT).as_posix(), "bytes": ZIP.stat().st_size,
                "sha256": sha256(ZIP), "page_count": None,
                "page_count_note": "Not applicable to an archive."},
    }
    manifest = {
        "schema_version": 1,
        "status": "NOT_VERIFIED",
        "build_input_commit": build_input_commit,
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "build_command": ["python", "scripts/build_submission.py",
                          "--max-main-pages", str(args.max_main_pages)],
        "tool_versions": versions,
        "max_main_pages": args.max_main_pages,
        "artifacts": artifacts,
        "checks": {
            "docx_exists": "PASS",
            "docx_sha256": "PASS",
            "docx_integrity": "PASS",
            "pdf_page_check": "PASS",
            "pdf_visual_inspection": "PENDING_MANUAL",
            "zip_integrity": "PASS",
            "zip_contents": "PASS",
            "unzip_t": "PASS",
        },
        "verification_policy": (
            "Package remains NOT_VERIFIED until a person visually inspects the final PDF and runs "
            "scripts/check_submission_manifest.py --confirm-pdf-visual-inspection."
        ),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("\nSubmission files:")
    for path in (DOCX, PDF, ZIP):
        print(f"- {path.relative_to(ROOT)} — {path.stat().st_size:,} bytes — SHA-256 {sha256(path)}")
    print(f"- {MANIFEST.relative_to(ROOT)} — NOT_VERIFIED pending visual PDF inspection")
    raw.unlink(missing_ok=True)
    fixed.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
