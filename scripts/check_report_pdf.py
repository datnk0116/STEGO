#!/usr/bin/env python3
"""Check PDF total pages and assignment main-body page limit."""
from __future__ import annotations
import argparse
import re
import subprocess
from pathlib import Path


def page_with_heading(pages: list[str], heading: str, start: int = 0) -> int | None:
    for index in range(start, len(pages)):
        lines = [line.strip() for line in pages[index].splitlines() if line.strip()]
        if heading in lines:
            return index
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--max-main-pages", type=int, default=17)
    args = parser.parse_args()
    if not args.pdf.is_file():
        parser.error(f"PDF not found: {args.pdf}")

    info = subprocess.run(
        ["pdfinfo", str(args.pdf)], capture_output=True, text=True, check=True
    ).stdout
    match = re.search(r"^Pages:\s+(\d+)", info, re.M)
    total = int(match.group(1)) if match else None
    if total is None:
        print("FAIL: pdfinfo did not report a page count.")
        return 2

    extracted = subprocess.run(
        ["pdftotext", "-layout", str(args.pdf), "-"],
        capture_output=True, text=True, check=True
    ).stdout
    pages = extracted.split("\f")
    summary_page = page_with_heading(pages, "Tóm tắt")
    refs_page = (
        page_with_heading(pages, "Tài liệu tham khảo", summary_page + 1)
        if summary_page is not None else None
    )
    if summary_page is None or refs_page is None:
        print(f"PDF total pages: {total}")
        print("FAIL: could not locate standalone headings Tóm tắt and Tài liệu tham khảo.")
        return 2

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
