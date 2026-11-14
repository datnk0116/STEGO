#!/usr/bin/env python3
"""Normalize Pandoc DOCX tables, math fallbacks and metadata for A4 export."""
from __future__ import annotations
import argparse
from pathlib import Path
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.shared import Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def child(parent, tag):
    node = parent.find(qn(tag))
    if node is None:
        node = OxmlElement(tag)
        parent.append(node)
    return node

def set_width(cell, dxa: int):
    node = child(cell._tc.get_or_add_tcPr(), "w:tcW")
    node.set(qn("w:w"), str(dxa)); node.set(qn("w:type"), "dxa")

def set_margins(cell, top=70, start=100, bottom=70, end=100):
    mar = child(cell._tc.get_or_add_tcPr(), "w:tcMar")
    for side, value in (("top",top),("start",start),("bottom",bottom),("end",end)):
        node = child(mar, f"w:{side}")
        node.set(qn("w:w"), str(value)); node.set(qn("w:type"), "dxa")

def shade(cell, fill):
    node = child(cell._tc.get_or_add_tcPr(), "w:shd")
    node.set(qn("w:fill"), fill); node.set(qn("w:val"), "clear")

def set_borders(table, color="B7C9D6", size="5"):
    borders = child(table._tbl.tblPr, "w:tblBorders")
    for edge in ("top","left","bottom","right","insideH","insideV"):
        node = child(borders, f"w:{edge}")
        node.set(qn("w:val"),"single"); node.set(qn("w:sz"),size)
        node.set(qn("w:space"),"0"); node.set(qn("w:color"),color)

def widths_for(matrix, total):
    n=len(matrix[0]); header=" ".join(matrix[0]).lower()
    if n==2: weights=[0.31,0.69]
    elif n==3 and "tiêu chí" in header: weights=[0.28,0.13,0.59]
    elif n==3 and "phương án" in header: weights=[0.22,0.38,0.40]
    elif n==3 and "biến thể" in header: weights=[0.23,0.36,0.41]
    elif n==3 and "khía cạnh" in header: weights=[0.22,0.39,0.39]
    elif n==3: weights=[0.22,0.35,0.43]
    elif n==4 and "mean" in header: weights=[0.12,0.18,0.43,0.27]
    elif n==4: weights=[0.27,0.23,0.22,0.28]
    else: weights=[1/n]*n
    raw=[max(700,round(total*w)) for w in weights]
    factor=total/sum(raw); result=[round(v*factor) for v in raw]
    result[-1]+=total-sum(result)
    return result

def remove_empty_toc(doc):
    body=doc._element.body
    for sdt in list(body.findall(qn("w:sdt"))):
        galleries=sdt.findall(".//"+qn("w:docPartGallery"))
        if any(g.get(qn("w:val"))=="Table of Contents" for g in galleries):
            body.remove(sdt)

def replace_math_fallbacks(doc):
    replacements={
      "[ S = E(C,M,K,) ]":"S = E(C, M, K, θ)",
      "[ M = D(S,K,) ]":"M̂ = D(S, K, θ)",
      "[ s =   ]":"s = ⌊512 / L⌋",
      "[ R_i = [is,(i+1)s)=_{n=0}{N-1}x[n]e{-j2kn/N} ]":"Rᵢ = [i·s, (i+1)·s) × [i·s, (i+1)·s)",
    }
    for p in doc.paragraphs:
        value=p.text.strip()
        if value in replacements:
            p.clear(); run=p.add_run(replacements[value])
            run.italic=True; run.font.name="Noto Sans"; run.font.size=Pt(10)
            p.paragraph_format.left_indent=Pt(18)
            p.paragraph_format.space_before=Pt(2); p.paragraph_format.space_after=Pt(5)

def tune_paragraphs(doc):
    for p in doc.paragraphs:
        if p.style.name in ("Normal","Body Text","First Paragraph"):
            p.paragraph_format.space_after=Pt(2.5)
            p.paragraph_format.line_spacing=1.02
            p.paragraph_format.widow_control=True
        if p.style.name.startswith("Heading"):
            p.paragraph_format.keep_with_next=True
            p.paragraph_format.keep_together=True
            p.paragraph_format.space_before=Pt(5 if p.style.name!="Heading 1" else 7)
            p.paragraph_format.space_after=Pt(2.5)

def rebuild_tables(doc):
    section=doc.sections[0]
    total_emu=section.page_width-section.left_margin-section.right_margin
    total_dxa=int(round(total_emu/635))
    for old in list(doc.tables):
        matrix=[[c.text.replace("\\n"," ").strip() for c in row.cells] for row in old.rows]
        if not matrix or not matrix[0]: continue
        new=doc.add_table(rows=len(matrix),cols=len(matrix[0]))
        new.alignment=WD_TABLE_ALIGNMENT.CENTER; new.autofit=False
        widths=widths_for(matrix,total_dxa)
        props=new._tbl.tblPr
        width_node=child(props,"w:tblW")
        width_node.set(qn("w:w"),str(total_dxa)); width_node.set(qn("w:type"),"dxa")
        layout=child(props,"w:tblLayout"); layout.set(qn("w:type"),"fixed")
        grid=new._tbl.tblGrid
        for e in list(grid): grid.remove(e)
        for width in widths:
            col=OxmlElement("w:gridCol"); col.set(qn("w:w"),str(width)); grid.append(col)
        for ri,row in enumerate(new.rows):
            trpr=row._tr.get_or_add_trPr(); trpr.append(OxmlElement("w:cantSplit"))
            if ri==0:
                repeat=OxmlElement("w:tblHeader"); repeat.set(qn("w:val"),"true"); trpr.append(repeat)
            for ci,cell in enumerate(row.cells):
                cell.text=matrix[ri][ci]; set_width(cell,widths[ci]); set_margins(cell)
                cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                if ri==0: shade(cell,"DCEAF4")
                elif ri%2==0: shade(cell,"F7FAFC")
                for p in cell.paragraphs:
                    p.style=doc.styles["Normal"]
                    p.paragraph_format.space_before=Pt(0); p.paragraph_format.space_after=Pt(0)
                    p.paragraph_format.line_spacing=1.0
                    for run in p.runs:
                        run.font.name="Noto Sans"
                        run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"),"Noto Sans")
                        run.font.size=Pt(8.5); run.font.color.rgb=RGBColor(25,35,45)
                        if ri==0:
                            run.bold=True; run.font.color.rgb=RGBColor(31,78,121)
        set_borders(new)
        old._tbl.addprevious(new._tbl); old._tbl.getparent().remove(old._tbl)

def set_properties(doc):
    doc.core_properties.title="Phân tích và đánh giá kỹ thuật Steganography"
    doc.core_properties.subject="UET.CN3124 - Đồ án thực hành CTF Jeopardy"
    doc.core_properties.author="Sinh viên UET.CN3124"
    doc.core_properties.keywords="Steganography; Steganalysis; BYUCTF; ImaginaryCTF; UET.CN3124"

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input",type=Path); ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    if not args.input.is_file(): ap.error(f"DOCX not found: {args.input}")
    doc=Document(args.input)
    remove_empty_toc(doc); replace_math_fallbacks(doc); tune_paragraphs(doc)
    rebuild_tables(doc); set_properties(doc)
    args.out.parent.mkdir(parents=True,exist_ok=True); doc.save(args.out)

if __name__=="__main__": main()
