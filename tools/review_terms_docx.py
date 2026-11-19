# -*- coding: utf-8 -*-
"""生成某一分类的术语审校 docx（与序生体系 v13 格式一致）。

用法：
    python tools/review_terms_docx.py 元意识体系
    python tools/review_terms_docx.py 本体论模型 --version 1
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai.i18n import CATEGORY_EN, DEFINITION_NOTE_EN, EN_NOTE_EN  # noqa: E402
from mcai.ordering import front_rank, term_rank  # noqa: E402

THEORY = "元意识学说"
THEORY_EN = "（Meta-Consciousness Theory）"


def add_theory_en(text: str) -> str:
    if not text:
        return text
    if THEORY + THEORY_EN in text:
        return text
    return text.replace(THEORY, THEORY + THEORY_EN)


def set_font(run, name="宋体", size=10.5, bold=False):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold


def para(doc, text="", size=10.5, font="宋体", indent=True, after=2):
    p = doc.add_paragraph()
    r = p.add_run(text)
    set_font(r, font, size)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.first_line_indent = Pt(21) if indent else Pt(0)
    return p


def field(doc, label: str, value: str = "", after=2):
    p = doc.add_paragraph()
    r1 = p.add_run(label)
    set_font(r1, "黑体", 10.5, True)
    if value:
        r2 = p.add_run(value)
        set_font(r2, "宋体", 10.5, False)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.first_line_indent = Pt(0)
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("category")
    ap.add_argument("--version", type=int, default=1)
    args = ap.parse_args()

    kb = json.loads((ROOT / "data" / "kb.json").read_text(encoding="utf-8"))
    terms = [c for c in kb["concepts"] if c.get("category") == args.category]
    if not terms:
        print("没有这个分类：", args.category)
        return 1
    terms.sort(key=lambda c: (term_rank(c["term"]), front_rank(c["term"]), c["term"]))

    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Cm(2.5)
    sec.bottom_margin = Cm(2.5)
    sec.left_margin = Cm(2.6)
    sec.right_margin = Cm(2.6)
    normal = doc.styles["Normal"]
    normal.font.name = "宋体"
    normal.font.size = Pt(10.5)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    normal.paragraph_format.line_spacing = 1.5

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"{args.category} · 术语审校（{len(terms)} 条）")
    set_font(r, "黑体", 18, True)
    p.paragraph_format.space_after = Pt(12)

    cat_en = CATEGORY_EN.get(args.category, "")

    for i, c in enumerate(terms, 1):
        h = doc.add_heading(level=2)
        hr = h.add_run(f"{i}. {c.get('term', '')}")
        set_font(hr, "黑体", 13, True)

        en = (c.get("en") or "").strip()
        if en:
            p = doc.add_paragraph()
            r1 = p.add_run("英文：")
            set_font(r1, "黑体", 10.5, True)
            r2 = p.add_run(en)
            set_font(r2, "宋体", 10.5, False)
            r3 = p.add_run(f"（{EN_NOTE_EN}）")
            set_font(r3, "宋体", 9, False)
            p.paragraph_format.first_line_indent = Pt(0)
            p.paragraph_format.space_after = Pt(2)

        if cat_en:
            p = doc.add_paragraph()
            r1 = p.add_run("所属体系：")
            set_font(r1, "黑体", 10.5, True)
            r2 = p.add_run(f"{args.category}（{cat_en}）")
            set_font(r2, "宋体", 10.5, False)
            r3 = p.add_run(f"（{EN_NOTE_EN}）")
            set_font(r3, "宋体", 9, False)
            p.paragraph_format.first_line_indent = Pt(0)
            p.paragraph_format.space_after = Pt(2)
        else:
            field(doc, "所属体系：", args.category)

        aliases = c.get("aliases") or []
        if aliases:
            field(doc, "别名：", "、".join(aliases))

        field(doc, "定义：")
        para(doc, add_theory_en(c.get("definition") or ""))
        note = f"（定义以中文为准，英文术语名为机译，仅供参考 / {DEFINITION_NOTE_EN}）"
        para(doc, note, size=9, indent=False, after=4)

        short = (c.get("short_definition") or "").strip()
        if short and short != (c.get("definition") or "").strip():
            field(doc, "简短定义：")
            para(doc, add_theory_en(short))

        if c.get("editor_note"):
            field(doc, "编者注：")
            para(doc, add_theory_en(c["editor_note"]))

        srcs = c.get("sources") or []
        if srcs:
            field(doc, "出处：", f"共 {len(srcs)} 条")
            for s in srcs[:3]:
                title = add_theory_en(s.get("doc_title", ""))
                section = add_theory_en(s.get("section", ""))
                line = f"· {title}"
                if section:
                    line += f"｜{section}"
                if s.get("location"):
                    line += f"｜{s['location']}"
                if s.get("char_start") is not None:
                    line += f"｜字符 {s.get('char_start')}–{s.get('char_end')}"
                para(doc, line, size=9, indent=False)
        else:
            field(doc, "出处：", "（无）")

        field(doc, "审校说明（一句话：结论 + 理由）：", after=8)
        para(doc, "", indent=False, after=8)

    out = ROOT / "docs" / "审校" / f"{args.category}-术语审校-v{args.version}.docx"
    doc.save(out)
    print(out)
    print("terms", len(terms))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
