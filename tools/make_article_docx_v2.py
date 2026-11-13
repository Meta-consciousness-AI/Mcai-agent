# -*- coding: utf-8 -*-
"""按第一稿内容重排文章版式（不改内容，只做结构化排版）。"""
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, Cm

SRC = Path(r"C:\Users\HP\Desktop\一个原创学说，怎么变成 AI 能调用的资产（第一稿）.docx")
OUT = Path(r"C:\Users\HP\Documents\deepseek-harness\default-workspace\mca-agent\docs\文章-学说变成可调用资产-第二稿排版.docx")

HEADINGS = {
    "先把学说拆成术语表",
    "让每条定义绑定出处",
    "再做成 AI 可调用的知识包",
    "接着分发到 AI 能找到的地方",
    "同时也做学术存证",
    "一个去作者化的设计",
    "一个可复制的教程",
    "九、这个知识库的现状与结构",
    "这个知识库的现状与结构",
    "附一：入口",
    "附二：参考实现（最小命令集）",
    "附三：数据口径与核验方法",
}
STEP = re.compile(r"^第\s*\d+\s*步：")
CODE = re.compile(r"^(pip install |mcai build |mcai mcp |学说 → )")
NUM_ITEM = re.compile(r"^\d+\s*(个|组|条)")
NOT_BULLET = (
    "所以", "最终", "每个", "分类", "这一步", "这一条", "这些", "去作者化",
    "这件事", "诚实", "链路", "回头", "单层", "我们", "知识包", "软件包",
    "术语表", "有了", "传播", "问题是", "怎么", "一个", "一套", "任何",
    "它", "其", "而", "但", "这", "在", "对", "从", "为", "如果", "当",
    "只", "先", "再", "接着", "同时", "也", "还", "即", "主要", "其次",
    "因此", "于是", "也就是说", "换句话说",
)


def is_bullet(text: str) -> bool:
    if len(text) > 45:
        return False
    if not (text.endswith("；") or text.endswith("。")):
        return False
    if NUM_ITEM.match(text):
        return True
    if text.startswith(NOT_BULLET):
        return False
    return True


def set_cn(run, font_cn, size, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font_cn)


src = Document(str(SRC))
paras = [p.text.strip() for p in src.paragraphs if p.text.strip()]

doc = Document()
sec = doc.sections[0]
sec.page_width = Cm(21)
sec.page_height = Cm(29.7)
for attr in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, attr, Cm(2.54))

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(12)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

for idx, text in enumerate(paras):
    if idx == 0:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cn(p.add_run(text), "黑体", 18, True)
        p.paragraph_format.space_after = Pt(18)
        continue

    if text.startswith("数据与事实截止"):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cn(p.add_run(text), "楷体", 10.5)
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(6)
        continue

    heading = text if text in HEADINGS else None
    if heading:
        clean = re.sub(r"^[一二三四五六七八九十]+、", "", heading)
        p = doc.add_paragraph()
        set_cn(p.add_run(clean), "黑体", 15, True)
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.keep_with_next = True
        continue

    if STEP.match(text):
        p = doc.add_paragraph()
        set_cn(p.add_run(text), "黑体", 13, True)
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        continue

    if CODE.match(text):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        set_cn(p.add_run(text), "Consolas", 10.5)
        continue

    if is_bullet(text):
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(2)
        set_cn(p.add_run(text), "宋体", 12)
        continue

    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(24)
    set_cn(p.add_run(text), "宋体", 12)

doc.save(str(OUT))
print("saved", OUT, "paras", len(doc.paragraphs))
