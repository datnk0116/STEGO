#!/usr/bin/env python3
"""Check PDF page count and the assignment's 15-page main-body limit."""
from __future__ import annotations
import argparse, re, subprocess
from pathlib import Path

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf",type=Path)
    parser.add_argument("--max-main-pages",type=int,default=15)
    args=parser.parse_args()
    if not args.pdf.is_file(): parser.error(f"PDF not found: {args.pdf}")
    info=subprocess.run(["pdfinfo",str(args.pdf)],capture_output=True,text=True,check=True).stdout
    match=re.search(r"^Pages:\s+(\d+)",info,re.M)
    total=int(match.group(1)) if match else None
    extracted=subprocess.run(["pdftotext","-layout",str(args.pdf),"-"],capture_output=True,text=True,check=True).stdout
    pages=extracted.split("\f")
    # Match standalone section headings, not the table-of-contents entries.
    summary_page=next((i for i,p in enumerate(pages) if re.search(r"(?m)^\\s*Tóm tắt\\s*$",p)),None)
    refs_page=next((i for i,p in enumerate(pages) if summary_page is not None and i>summary_page and re.search(r"(?m)^\\s*Tài liệu tham khảo\\s*$",p)),None)
    main_pages=(refs_page-summary_page) if summary_page is not None and refs_page is not None else None
    print(f"PDF total pages: {total}")
    print(f"Main-body pages (from Tóm tắt to before Tài liệu tham khảo): {main_pages}")
    if main_pages is None:
        print("WARNING: could not detect main-body boundaries automatically.")
        return 0
    if main_pages>args.max_main_pages:
        print(f"FAIL: main body exceeds {args.max_main_pages} pages.")
        return 2
    print("PASS: main body satisfies the assignment page limit.")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
