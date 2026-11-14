#!/usr/bin/env python3
"""Verify total PDF pages and estimate main-body pages from extracted text."""
from __future__ import annotations
import argparse
import re
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--max-main-pages", type=int, default=15)
    args = parser.parse_args()
    if not args.pdf.is_file():
        parser.error(f"PDF not found: {args.pdf}")

    info = subprocess.run(
        ["pdfinfo", str(args.pdf)], capture_output=True, text=True, check=True
    ).stdout
    match = re.search(r"^Pages:\s+(\d+)", info, re.M)
    total = int(match.group(1)) if match else None

    extracted = subprocess.run(
        ["pdftotext", "-layout", str(args.pdf), "-"],
        capture_output=True, text=True, check=True
    ).stdout
    summary_index = extracted.find("Tóm tắt")
    refs_index = extracted.find("Tài liệu tham khảo", summary_index + 1) if summary_index >= 0 else -1
    if summary_index < 0 or refs_index < 0:
        print(f"PDF total pages: {total}")
        print("FAIL: could not find the main-body boundaries (Tóm tắt / Tài liệu tham khảo).")
        return 2

    summary_page = extracted[:summary_index].count("\f") + 1
    refs_page = extracted[:refs_index].count("\f") + 1
    main_pages = refs_page - summary_page
    print(f"PDF total pages: {total}")
    print(f"Main-body pages (Tóm tắt through page before references): {main_pages}")
    if main_pages > args.max_main_pages:
        print(f"FAIL: main body exceeds {args.max_main_pages} pages.")
        return 2
    print("PASS: main body satisfies the assignment page limit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
