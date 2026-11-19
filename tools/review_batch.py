# -*- coding: utf-8 -*-
"""按分类抽取审校批次，生成 xlsx 审校包。

用法：
    python tools/review_batch.py 序生体系
    python tools/review_batch.py 本体论模型
"""
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "data" / "kb.json"
OUT_DIR = ROOT / "docs" / "审校"


def load():
    return json.loads(KB.read_text(encoding="utf-8"))


def collect(kb, category):
    terms = [c for c in kb["concepts"] if c.get("category") == category]
    names = {c["term"] for c in terms}
    faqs = [
        f for f in kb["faqs"]
        if names & set((f.get("related") or []) + (f.get("source_terms") or []))
    ]
    relations = []
    for c in terms:
        for r in c.get("relations", []):
            relations.append((c["term"], r))
    relations += [
        (c["term"], r) for c in kb["concepts"]
        if c["term"] not in names
        for r in c.get("relations", [])
        if r.get("target") in names
    ]
    return terms, faqs, relations


def header(ws, cols):
    fill = PatternFill("solid", fgColor="D9E1F2")
    for i, name in enumerate(cols, 1):
        cell = ws.cell(row=1, column=i, value=name)
        cell.font = Font(bold=True)
        cell.fill = fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)


def validate(ws, col, n):
    dv = DataValidation(type="list", formula1='"保留,修改,删除,新增,待定"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{col}2:{col}{n}")


def main():
    category = sys.argv[1] if len(sys.argv) > 1 else "序生体系"
    kb = load()
    terms, faqs, relations = collect(kb, category)
    if not terms:
        print("没有这个分类：", category)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{category}-审校包.xlsx"
    wb = Workbook()

    ws = wb.active
    ws.title = "说明"
    for i, line in enumerate([
        f"{category} 审校包",
        "",
        f"术语 {len(terms)} 条，关联问答 {len(faqs)} 条，关联关系 {len(relations)} 条。",
        "",
        "顺序：术语 → 问答 → 关系。",
        "结论列：保留 / 修改 / 删除 / 新增 / 待定。",
        "修改的，在「修改后」列写新文本，理由写一句。",
    ], 1):
        ws.cell(row=i, column=1, value=line)

    ws1 = wb.create_sheet("术语")
    cols = ["序号", "术语", "分类", "类型", "定义", "简短定义", "编者注", "英文", "别名", "出处数",
            "审校结论", "修改后定义", "修改后简短定义", "修改理由"]
    header(ws1, cols)
    for i, c in enumerate(terms, 1):
        ws1.append([i, c.get("term"), c.get("category"), c.get("kind"), c.get("definition"),
                    c.get("short_definition"), c.get("editor_note"), c.get("en"),
                    ",".join(c.get("aliases") or []), len(c.get("sources") or []),
                    "", "", "", ""])
    ws1.freeze_panes = "C2"
    ws1.column_dimensions["E"].width = 60
    ws1.column_dimensions["F"].width = 40
    validate(ws1, "K", ws1.max_row)

    ws2 = wb.create_sheet("问答")
    cols = ["序号", "id", "问题", "简短回答", "完整回答", "关联术语", "审校结论", "修改后回答", "修改理由"]
    header(ws2, cols)
    for i, f in enumerate(faqs, 1):
        ws2.append([i, f.get("id"), f.get("question"), f.get("short_answer"), f.get("answer"),
                    ",".join((f.get("related") or []) + (f.get("source_terms") or [])),
                    "", "", ""])
    ws2.freeze_panes = "C2"
    ws2.column_dimensions["E"].width = 70
    validate(ws2, "G", ws2.max_row)

    ws3 = wb.create_sheet("关系")
    cols = ["序号", "源术语", "关系类型", "目标术语", "层级", "依据原文", "审校结论", "修改后目标", "修改理由"]
    header(ws3, cols)
    for i, (src, r) in enumerate(relations, 1):
        ws3.append([i, src, r.get("type"), r.get("target"), r.get("tier"), r.get("evidence"), "", "", ""])
    ws3.freeze_panes = "C2"
    ws3.column_dimensions["F"].width = 60
    validate(ws3, "G", ws3.max_row)

    wb.save(out)
    print(out)
    print(f"terms={len(terms)} faqs={len(faqs)} relations={len(relations)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
