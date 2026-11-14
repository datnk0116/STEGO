#!/usr/bin/env python3
"""Build DOCX, PDF and source ZIP locally; this script does not invoke GitHub Actions."""
from __future__ import annotations
import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"results"/"submission"
DOCX=OUT/"STUDENT_UETCN3124_CTF_Report.docx"
PDF=OUT/"STUDENT_UETCN3124_CTF_Report.pdf"
ZIP=OUT/"STUDENT_UETCN3124_Scripts.zip"

def run(command):
    print("+"," ".join(map(str,command)),flush=True)
    subprocess.run(command,cwd=ROOT,check=True,text=True)

def require_tools(names):
    missing=[name for name in names if shutil.which(name) is None]
    if missing:
        raise SystemExit("Missing tools: "+", ".join(missing)+
          ". Install Pandoc, LibreOffice Writer and Poppler before building.")

def build_zip():
    top_files=["README.md","requirements.txt"]
    directories=["data","src","tests","scripts","references","report","results","docs"]
    excluded_parts={".venv","venv","__pycache__",".git"}
    excluded_suffixes={".pyc",".pyo",".tmp",".bak"}
    with zipfile.ZipFile(ZIP,"w",zipfile.ZIP_DEFLATED,compresslevel=8) as archive:
        for name in top_files:
            path=ROOT/name
            if path.is_file(): archive.write(path,path.relative_to(ROOT).as_posix())
        for dirname in directories:
            folder=ROOT/dirname
            if not folder.exists(): continue
            for path in sorted(folder.rglob("*")):
                if not path.is_file(): continue
                rel=path.relative_to(ROOT)
                if any(part in excluded_parts for part in rel.parts): continue
                if path.suffix.lower() in excluded_suffixes: continue
                if rel.parts[:2]==("results","submission"): continue
                if path.name in {".DS_Store",".env"}: continue
                archive.write(path,rel.as_posix())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-main-pages",type=int,default=15)
    args=parser.parse_args()
    require_tools(["pandoc","libreoffice","pdfinfo","pdftotext"])
    OUT.mkdir(parents=True,exist_ok=True)
    reference=OUT/"reference.docx"
    raw=OUT/"report-pandoc.docx"
    fixed=OUT/"report-fixed.docx"
    profile=Path("/tmp/lo-profile-stego-build")
    profile.mkdir(parents=True,exist_ok=True)
    run([sys.executable,str(ROOT/"scripts"/"create_reference_docx.py"),"--out",str(reference)])
    run(["pandoc",str(ROOT/"report"/"REPORT.md"),
      "--from=markdown+tex_math_dollars+pipe_tables",
      "--resource-path=.:report","--standalone",
      f"--reference-doc={reference}",
      "--metadata","lang=vi-VN",
      "--metadata","title=Phân tích và đánh giá kỹ thuật Steganography",
      "--metadata","author=Sinh viên UET.CN3124",
      "--output",str(raw)])
    run([sys.executable,str(ROOT/"scripts"/"fix_report_docx.py"),str(raw),"--out",str(fixed)])
    shutil.copy2(fixed,DOCX)
    PDF.unlink(missing_ok=True)
    run(["libreoffice",f"-env:UserInstallation=file://{profile}","--headless",
         "--convert-to","pdf","--outdir",str(OUT),str(DOCX)])
    run([sys.executable,str(ROOT/"scripts"/"check_report_pdf.py"),
         str(PDF),"--max-main-pages",str(args.max_main_pages)])
    info=subprocess.run(["pdfinfo",str(PDF)],check=True,text=True,capture_output=True).stdout
    (OUT/"pdf-metadata.txt").write_text(info,encoding="utf-8")
    build_zip()
    print("\\nSubmission files:")
    for path in (DOCX,PDF,ZIP):
        print(f"- {path.relative_to(ROOT)} — {path.stat().st_size:,} bytes")
    raw.unlink(missing_ok=True); fixed.unlink(missing_ok=True)

if __name__=="__main__": main()
