# -*- coding: utf-8 -*-
"""构建引用忠实度评测集（四个层级）。

层级：
- exact：直接问「什么是 X？」
- paraphrase：用定义改写提问，不出现术语名
- homonym：近义/同名混淆，期望回答区分而不是拒答
- refusal：库外问题，期望明确说不知道

输出：benchmark/citation-faithfulness/items.jsonl
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
KB = ROOT / "data" / "kb.json"
OUT = ROOT / "benchmark" / "citation-faithfulness" / "items.jsonl"

def extract_clause(definition: str, term: str) -> str:
    """从定义原文取一个不包含术语名的句子，作为改写提问。"""
    parts = re.split(r"[，。；：、,.;:！？!?（）()]", definition or "")
    parts = [p.strip() for p in parts if p and p.strip()]
    parts = [p for p in parts if term not in p and len(p) >= 8]
    return max(parts, key=len) if parts else ""


PARAPHRASE_SLUGS = [
    "meta-consciousness", "meta-recognition", "meta-knowledge",
    "observation-creates-reality", "meta-network", "progenerative-agent",
    "meta-knowledge-property", "meta-knowledge-society", "meta-being",
    "phenomenal-space-time",
]

HOMONYM = [
    ("meta-consciousness", "心理学中的 meta-awareness 与你们说的元意识是同一个概念吗？"),
    ("observation-creates-reality", "量子力学的观测者效应，就是你们说的观测创造实在吗？"),
    ("progenerative-agent", "通用 AI Agent 就是序生智能体吗？"),
    ("meta-knowledge", "知识管理和你们说的元知是一回事吗？"),
]

SEMANTIC = [
    ("meta-consciousness", "世界最开始的那个东西是什么？"),
    ("observation-creates-reality", "没人看的时候，事物还存在吗？"),
    ("meta-recognition", "我们认识世界这件事，本身叫什么？"),
    ("meta-knowledge", "想明白之后固定下来的东西，叫什么？"),
    ("meta-network", "万事万物之间是怎么连起来的？"),
    ("progenerative-agent", "以后会不会出现不是碳基的观察者？"),
    ("meta-knowledge-property", "想法被别人拿去用，怎么保护？"),
    ("meta-knowledge-society", "如果知识能当钱用，社会会变成什么样？"),
    ("meta-being", "在宇宙里能认知世界的个体，算什么单位？"),
    ("phenomenal-space-time", "我们看到的这个时空，是怎么来的？"),
]

HELDOUT = [
    ("meta-consciousness", "宇宙的第一因是什么？"),
    ("observation-creates-reality", "闭上眼睛，世界还在吗？"),
    ("meta-knowledge-society", "知识能换钱的社会是什么样？"),
    ("progenerative-agent", "从宇宙演化中长出来的智能体是什么？"),
    ("phenomenal-space-time", "我们感知到的现实世界是怎么形成的？"),
]

NEGATIVES = [
    "今天北京天气怎么样？",
    "帮我推荐一只明天会涨的股票。",
    "我最近失眠，应该吃什么药？",
    "请写一段 Python 快速排序代码。",
    "2026 年诺贝尔文学奖得主是谁？",
    "如何申请护照？",
    "解释一下量子纠缠的数学推导。",
    "给我一份减脂食谱。",
    "红楼梦的作者是谁？",
    "明天适合搬家吗？",
]


def main():
    kb = json.loads(KB.read_text(encoding="utf-8"))
    by_slug = {c["slug"]: c for c in kb.get("concepts", [])}
    items = []

    def source_list(c):
        return [
            {"doc_id": s.get("doc_id"), "location": s.get("location"),
             "quote": s.get("quote", ""), "char_start": s.get("char_start"),
             "char_end": s.get("char_end")}
            for s in c.get("sources", []) if s.get("origin") != "curated"
        ]

    def allowed_list(c):
        rows = [
            {"doc_id": s.get("doc_id"), "location": s.get("location"),
             "quote": s.get("quote", "")}
            for s in c.get("sources", [])
        ]
        rows += [{"doc_id": e.get("doc_id"), "location": e.get("location"),
                  "quote": e.get("quote", "")}
                 for e in c.get("evidence", [])]
        return rows

    for c in kb.get("concepts", []):
        gold = source_list(c)
        if not gold:
            continue
        items.append({
            "id": "exact-" + c["slug"],
            "tier": "exact",
            "question": f"什么是{c['term']}？",
            "term": c["term"],
            "gold_answer": c.get("definition", ""),
            "gold_sources": gold,
            "allowed_sources": allowed_list(c),
        })

    for slug in PARAPHRASE_SLUGS:
        c = by_slug.get(slug)
        if not c:
            continue
        clause = extract_clause(c.get("definition", ""), c["term"])
        if not clause:
            continue
        q = f"「{clause}」——这说的是哪个概念？"
        items.append({
            "id": "paraphrase-" + slug,
            "tier": "paraphrase",
            "question": q,
            "term": c["term"],
            "gold_answer": c.get("definition", ""),
            "gold_sources": source_list(c),
            "allowed_sources": allowed_list(c),
        })

    for slug, q in HOMONYM:
        c = by_slug.get(slug)
        if not c:
            continue
        items.append({
            "id": "homonym-" + slug,
            "tier": "homonym",
            "question": q,
            "term": c["term"],
            "gold_answer": c.get("definition", ""),
            "gold_sources": [],
            "allowed_sources": allowed_list(c),
        })

    for slug, q in SEMANTIC:
        c = by_slug.get(slug)
        if not c:
            continue
        items.append({
            "id": "semantic-" + slug,
            "tier": "semantic",
            "question": q,
            "term": c["term"],
            "gold_answer": c.get("definition", ""),
            "gold_sources": source_list(c),
            "allowed_sources": allowed_list(c),
        })

    for slug, q in HELDOUT:
        c = by_slug.get(slug)
        if not c:
            continue
        items.append({
            "id": "heldout-" + slug,
            "tier": "semantic-heldout",
            "question": q,
            "term": c["term"],
            "gold_answer": c.get("definition", ""),
            "gold_sources": source_list(c),
            "allowed_sources": allowed_list(c),
        })

    for i, q in enumerate(NEGATIVES, 1):
        items.append({
            "id": f"refusal-{i:02d}",
            "tier": "refusal",
            "question": q,
            "term": "",
            "gold_answer": "",
            "gold_sources": [],
            "allowed_sources": [],
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    from collections import Counter
    print("items", len(items), dict(Counter(x["tier"] for x in items)))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
