# -*- coding: utf-8 -*-
"""把文章正文纯文本排成 docx，便于阅读与批注。"""
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, Cm

ROOT = Path(r"C:\Users\HP\Documents\deepseek-harness\default-workspace\mca-agent")
SRC = ROOT / "docs" / "文章-学说变成可调用资产-正文.txt"
OUT = ROOT / "docs" / "文章-学说变成可调用资产-正文.docx"

text = SRC.read_text(encoding="utf-8")
lines = [ln.rstrip() for ln in text.splitlines()]

HEAD1 = re.compile(r"^([一二三四五六七八九十]+、|附[一二三]：)")
HEAD1_BARE = re.compile(r"^[一二三四五六七八九十]$")
HEAD2 = re.compile(r"^第\s*\d+\s*步：")


def set_cn(run, font_cn, size, bold=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    r = run._element.rPr.rFonts
    r.set(qn("w:eastAsia"), font_cn)


doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21)
sec.page_height = Cm(29.7)
sec.left_margin = Cm(2.54)
sec.right_margin = Cm(2.54)
sec.top_margin = Cm(2.54)
sec.bottom_margin = Cm(2.54)

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(12)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

first = True
for raw in lines:
    line = raw.strip()
    if not line:
        continue
    if first:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cn(p.add_run(line), "黑体", 18, True)
        p.paragraph_format.space_after = Pt(12)
        first = False
        continue
    if line.startswith("数据与事实截止"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cn(p.add_run(line), "楷体", 10.5)
        p.paragraph_format.space_after = Pt(18)
        continue
    if HEAD2.match(line):
        p = doc.add_paragraph()
        set_cn(p.add_run(line), "黑体", 13, True)
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        continue
    if HEAD1.match(line) or HEAD1_BARE.match(line):
        p = doc.add_paragraph()
        set_cn(p.add_run(line), "黑体", 15, True)
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(8)
        continue
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(24)
    set_cn(p.add_run(line), "宋体", 12)

doc.save(str(OUT))
print("saved", OUT, "paras", len(doc.paragraphs))
