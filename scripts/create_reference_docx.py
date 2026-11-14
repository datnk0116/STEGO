#!/usr/bin/env python3
"""Create a Pandoc reference DOCX with consistent UET-style document formatting."""
from __future__ import annotations
import argparse
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_run_font(run, name: str, size: float, bold: bool=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)

def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr_text)
    run._r.append(fld_char2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.3)
    section.right_margin = Cm(2.0)
    section.header_distance = Cm(0.9)
    section.footer_distance = Cm(0.9)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Noto Sans"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Noto Sans")
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.12

    for name, size, color in [
        ("Title", 18, (31, 55, 86)),
        ("Heading 1", 15, (31, 78, 121)),
        ("Heading 2", 12, (46, 96, 145)),
        ("Heading 3", 11, (68, 84, 106)),
    ]:
        style = styles[name]
        style.font.name = "Noto Sans"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Noto Sans")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(*color)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.space_before = Pt(10)
        style.paragraph_format.space_after = Pt(5)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_run_font(header.add_run("UET.CN3124 | ĐỒ ÁN THỰC HÀNH CTF JEOPARDY"), "Noto Sans", 8, color=(100, 110, 120))
    footer = section.footer.paragraphs[0]
    add_page_number(footer)
    for run in footer.runs:
        set_run_font(run, "Noto Sans", 8, color=(100, 110, 120))

    # Pandoc will use paragraph/table styles from this reference document.
    for table_style_name in ("Table Grid", "Table"):
        try:
            table = styles[table_style_name]
            table.font.name = "Noto Sans"
            table._element.rPr.rFonts.set(qn("w:eastAsia"), "Noto Sans")
            table.font.size = Pt(9)
            break
        except KeyError:
            continue
    args.out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(args.out)

if __name__ == "__main__":
    main()
