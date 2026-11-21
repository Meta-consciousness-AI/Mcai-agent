# -*- coding: utf-8 -*-
"""逐条审校 122 条问答与 270 条关系，输出工作簿。

用法：python tools/audit_faq_relations.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai.corpus import load_corpus  # noqa: E402

BANNED = ["节拍面", "空间的元实体", "时间的元实体"]
OLD = ["观测元时空", "意识层面", "新纪元", "觉醒度"]
REIFY = [r"空间是.{0,6}实体", r"时间是.{0,6}实体", r"元实体.{0,6}(空间|时间)"]


def flags_for_faq(f, terms):
    flags = []
    text = f["question"] + " " + f.get("answer", "")
    for w in BANNED:
        if w in text:
            flags.append(f"禁用术语：{w}")
    for w in OLD:
        if w == "意识层面":
            if re.search(r"(?<!元)意识层面", text):
                flags.append("旧表述：意识层面")
        elif w in text:
            flags.append(f"旧表述：{w}")
    for p in REIFY:
        if re.search(p, text):
            flags.append("疑似把时空说成实体")
    if "序生场" in text and "物理场" in text and not re.search(r"(不是|非)物理场", text):
        flags.append("序生场未加非物理场限定")
    if any(k in text for k in ("空间", "时间", "现象时空", "尺度面")) and "显化" in text:
        if not any(k in text for k in ("测创", "观测")):
            flags.append("显化未提测创/观测")
    related = f.get("related") or []
    lookup = {}
    for term, c in terms.items():
        lookup[term] = c
        if c.get("slug"):
            lookup[c["slug"]] = c
        if c.get("en"):
            lookup[c["en"].lower()] = c
    missing = [x for x in related if x not in lookup]
    if missing:
        flags.append("关联术语不存在：" + "、".join(missing))
    mentioned = False
    for x in related:
        c = lookup.get(x)
        if c and (c["term"] in text or (c.get("en") and c["en"] in text)):
            mentioned = True
            break
    if related and not mentioned:
        flags.append("答案未提及任一关联术语")
    if not f.get("answer", "").strip():
        flags.append("答案为空")
    return flags


def evidence_matches(evidence: str, blocks: list[str]) -> bool:
    """证据可以是多段原文，用空行分隔；每段都必须逐字回查。"""
    parts = [p.strip() for p in (evidence or "").split("\n\n") if p.strip()]
    return bool(parts) and all(any(p in b for b in blocks) for p in parts)


def flags_for_rel(src, r, terms, blocks):
    flags = []
    target = r.get("target", "")
    if target not in terms:
        flags.append("目标术语不存在")
    if target == src:
        flags.append("自指关系")
    if not (r.get("evidence") or "").strip():
        flags.append("缺证据")
    elif not evidence_matches(r["evidence"], blocks):
        flags.append("证据不能逐字回查")
    typ, tier = r.get("type"), r.get("tier")
    if typ == "提及" and tier in ("core", "derived"):
        flags.append("类型与层级不一致")
    if typ != "提及" and tier == "mention":
        flags.append("类型与层级不一致")
    if typ == "衍生自" and r.get("target") not in terms:
        flags.append("衍生父项不存在")
    return flags


def header(ws, cols):
    fill = PatternFill("solid", fgColor="D9E1F2")
    for i, c in enumerate(cols, 1):
        cell = ws.cell(row=1, column=i, value=c)
        cell.font = Font(bold=True)
        cell.fill = fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)


def main() -> int:
    kb = json.loads((ROOT / "data" / "kb.json").read_text(encoding="utf-8"))
    terms = {c["term"]: c for c in kb["concepts"]}
    corpus = load_corpus(str(ROOT / "config" / "corpus.json"))
    blocks = [b.text for d in corpus.documents for b in d.blocks]

    wb = Workbook()
    ws = wb.active
    ws.title = "问答"
    cols = ["序号", "id", "问题", "答案", "关联术语", "规则标记", "结论", "修改后答案", "审校说明"]
    header(ws, cols)
    faq_rows = []
    for i, f in enumerate(kb["faqs"], 1):
        flags = flags_for_faq(f, terms)
        verdict = "待审" if flags else "保留"
        ws.append([i, f["id"], f["question"], f["answer"],
                   "、".join(f.get("related") or []), "；".join(flags), verdict, "", ""])
        faq_rows.append({"id": f["id"], "flags": flags, "verdict": verdict})
    ws.freeze_panes = "C2"
    ws.column_dimensions["D"].width = 80
    ws.column_dimensions["F"].width = 40

    ws2 = wb.create_sheet("关系")
    cols2 = ["序号", "源术语", "类型", "目标术语", "层级", "证据", "规则标记", "结论", "修改建议", "审校说明"]
    header(ws2, cols2)
    rel_rows = []
    i = 0
    seen = set()
    for c in kb["concepts"]:
        for r in c.get("relations", []):
            i += 1
            flags = flags_for_rel(c["term"], r, terms, blocks)
            key = (c["term"], r.get("type"), r.get("target"))
            if key in seen:
                flags.append("重复关系")
            seen.add(key)
            verdict = "待审" if flags else "保留"
            ws2.append([i, c["term"], r.get("type"), r.get("target"), r.get("tier"),
                        r.get("evidence", ""), "；".join(flags), verdict, "", ""])
            rel_rows.append({"i": i, "src": c["term"], "type": r.get("type"),
                             "target": r.get("target"), "flags": flags, "verdict": verdict})
    ws2.freeze_panes = "C2"
    ws2.column_dimensions["F"].width = 60
    ws2.column_dimensions["G"].width = 40

    out = ROOT / "docs" / "审校" / "问答关系逐条审校-2026-11-20.xlsx"
    wb.save(out)
    print(out)
    print("faq", len(faq_rows), "待审", sum(1 for x in faq_rows if x["verdict"] == "待审"))
    print("rel", len(rel_rows), "待审", sum(1 for x in rel_rows if x["verdict"] == "待审"))
    (ROOT / "docs" / "审校" / "audit-flags.json").write_text(
        json.dumps({"faq": faq_rows, "rel": rel_rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
