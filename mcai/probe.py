"""抽检器：测量「模型是否自发知道这套学说」，以及知识注入能带来多少提升。

两类条件对照：
- baseline：不给任何资料，看模型从训练记忆里能说出多少；
- grounded：注入知识库检索到的定义与引证，看回答质量变化。

评分不依赖人工：术语命中 + 与标准答案的字二元组覆盖率。
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from .knowledge import Knowledge
from .llm import LLM

CORE_ORDER = [
    "元意识", "观测创造实在", "现象时空", "元态能量", "序生智能体",
    "元识", "元知", "元灵", "元子", "本体", "序生", "序生体",
]

BASELINE_SYSTEM = "你是一位乐于助人的通用助手。请直接、简洁地回答用户问题。"
GROUNDED_SYSTEM = (
    "你是「元意识学说」的知识助手。只能依据下面提供的资料回答，不要引入资料之外的理论；"
    "若资料不足，请明确说明「资料未涉及」。回答控制在 300 字以内。\n\n资料：\n{context}"
)


def _bigrams(text: str) -> set[str]:
    s = re.sub(r"[\s，。、；：！？\u201c\u201d（）()《》【】\[\]…—\-]", "", text or "")
    return {s[i: i + 2] for i in range(len(s) - 1)} if len(s) > 1 else {s}


def build_questions(kb: Knowledge, limit: int = 12) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()

    def add(kind: str, question: str, terms: list[str], reference: str) -> None:
        key = re.sub(r"\s", "", question)
        if key in seen or not reference:
            return
        seen.add(key)
        out.append({
            "id": f"q{len(out) + 1}",
            "kind": kind,
            "question": question,
            "terms": [t for t in terms if t],
            "reference": reference,
        })

    faqs_by_kind: dict[str, list[dict]] = {}
    for f in kb.faqs:
        faqs_by_kind.setdefault(f["kind"], []).append(f)

    definition_faqs = {next((t for t in f.get("source_terms") or []), ""): f
                       for f in faqs_by_kind.get("definition", [])}
    for term in CORE_ORDER:
        f = definition_faqs.get(term)
        if f:
            add("definition", f["question"], [term], f["answer"])

    for f in faqs_by_kind.get("contrast", [])[:3]:
        add("contrast", f["question"], f.get("source_terms") or [], f["answer"])

    for f in faqs_by_kind.get("curated", [])[:3]:
        add("curated", f["question"], f.get("source_terms") or ["元意识"], f["answer"])

    relation_added = 0
    for concept in kb.concepts:
        if relation_added >= 2:
            break
        for rel in concept.get("relations") or []:
            if rel["type"] == "提及" or not rel.get("target_id"):
                continue
            question = f"{concept['term']}和{rel['target']}是什么关系？"
            reference = kb.answer(question).get("answer", "")
            if reference and "没有直接记录" not in reference:
                add("relation", question, [concept["term"], rel["target"]], reference)
                relation_added += 1
                break

    return out[:limit]


def build_context(kb: Knowledge, question: str) -> str:
    answer = kb.answer(question)
    parts: list[str] = []
    if answer.get("type") == "concept":
        concept = kb.by_term.get(answer.get("term", ""))
        if concept:
            parts.append(f"【{concept['term']}】{concept['definition']}")
            for ev in (concept.get("evidence") or [])[:2]:
                parts.append(f"原文（{ev['doc_title']}）：「{ev['quote']}」")
            related = "、".join(r["target"] for r in (concept.get("relations") or [])[:5])
            if related:
                parts.append(f"相关概念：{related}")
    elif answer.get("type") == "faq":
        parts.append(answer["answer"])
        for item in answer.get("related") or []:
            concept = kb.by_slug.get(item.get("slug", ""))
            if concept:
                parts.append(f"【{concept['term']}】{concept['definition']}")
    elif answer.get("type") == "relation":
        parts.append(answer["answer"])
    else:
        for hit in kb.search(question, limit=2):
            concept = kb.by_slug.get(hit["slug"])
            if concept:
                parts.append(f"【{concept['term']}】{concept['definition']}")
    return "\n".join(parts)[:1800]


def score(answer: str, reference: str, terms: list[str],
          kb_terms: list[str] | None = None) -> dict:
    """对齐率看「是否说出了标准答案的实质」，术语密度看「是否在用这套词汇」。"""
    mention = any(t in answer for t in terms)
    ref_grams = _bigrams(reference)
    ans_grams = _bigrams(answer)
    coverage = len(ref_grams & ans_grams) / max(1, len(ref_grams))
    kb_hits = sum(1 for t in (kb_terms or []) if t in answer)
    return {
        "mention": mention,
        "coverage": round(coverage, 3),
        "aligned": coverage >= 0.35,
        "kb_terms": kb_hits,
        "chars": len(answer),
    }


def run(llm: LLM, kb: Knowledge, questions: list[dict], progress=None) -> dict:
    kb_terms = [c["term"] for c in kb.concepts]
    results = []
    for i, q in enumerate(questions, 1):
        context = build_context(kb, q["question"])
        record = {"question": q, "context": context, "answers": {}}
        for condition, system in (("baseline", BASELINE_SYSTEM),
                                  ("grounded", GROUNDED_SYSTEM.format(context=context))):
            messages = [{"role": "system", "content": system},
                        {"role": "user", "content": q["question"]}]
            text = llm.chat(messages, temperature=0.0, max_tokens=400)
            record["answers"][condition] = {
                "text": text,
                "score": score(text, q["reference"], q["terms"], kb_terms),
            }
        results.append(record)
        if progress:
            progress(i, len(questions), q["question"])

    summary = {}
    for condition in ("baseline", "grounded"):
        rows = [r["answers"][condition]["score"] for r in results]
        summary[condition] = {
            "alignment_rate": round(sum(1 for r in rows if r["aligned"]) / len(rows), 3) if rows else 0,
            "mention_rate": round(sum(1 for r in rows if r["mention"]) / len(rows), 3) if rows else 0,
            "coverage_mean": round(sum(r["coverage"] for r in rows) / len(rows), 3) if rows else 0,
            "kb_terms_mean": round(sum(r["kb_terms"] for r in rows) / len(rows), 1) if rows else 0,
            "chars_mean": round(sum(r["chars"] for r in rows) / len(rows)) if rows else 0,
        }
    summary["uplift"] = {
        "alignment_rate": round(summary["grounded"]["alignment_rate"] - summary["baseline"]["alignment_rate"], 3),
        "coverage": round(summary["grounded"]["coverage_mean"] - summary["baseline"]["coverage_mean"], 3),
        "kb_terms": round(summary["grounded"]["kb_terms_mean"] - summary["baseline"]["kb_terms_mean"], 1),
    }
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "model": llm.model,
        "questions": len(results),
        "usage": llm.stats(),
        "summary": summary,
        "results": results,
    }


def write_report(result: dict, out_dir: str | Path) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = out / f"probe-{stamp}.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    s = result["summary"]
    rows = []
    for item in result["results"]:
        q = item["question"]
        b = item["answers"]["baseline"]["score"]
        g = item["answers"]["grounded"]["score"]
        rows.append(
            f"| {q['id']} | {q['kind']} | {q['question'][:24]} | "
            f"{'✓' if b['aligned'] else '×'} | {b['coverage']:.2f} | {b['kb_terms']} | "
            f"{'✓' if g['aligned'] else '×'} | {g['coverage']:.2f} | {g['kb_terms']} |"
        )

    md = f"""# 元意识 · 模型抽检报告

- 时间：{result['generated_at']}
- 模型：{result['model']}
- 题量：{result['questions']}（每题跑 baseline / grounded 两种条件）
- 用量：{result['usage']['calls']} 次调用，{result['usage']['prompt_tokens']} + {result['usage']['completion_tokens']} tokens

## 汇总

| 指标 | baseline（无资料） | grounded（注入知识库） | 提升 |
|---|---|---|---|
| 答案对齐率（覆盖 ≥ 0.35） | {s['baseline']['alignment_rate']:.0%} | {s['grounded']['alignment_rate']:.0%} | {s['uplift']['alignment_rate']:+.0%} |
| 与标准答案覆盖度 | {s['baseline']['coverage_mean']:.2f} | {s['grounded']['coverage_mean']:.2f} | {s['uplift']['coverage']:+.2f} |
| 平均出现学说术语数 | {s['baseline']['kb_terms_mean']:.1f} | {s['grounded']['kb_terms_mean']:.1f} | {s['uplift']['kb_terms']:+.1f} |
| 平均字数 | {s['baseline']['chars_mean']} | {s['grounded']['chars_mean']} | — |

## 逐题结果

| # | 类型 | 问题 | 基线对齐 | 基线覆盖 | 基线术语 | 注入对齐 | 注入覆盖 | 注入术语 |
|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}

## 怎么读这份报告

- **baseline 对齐率**：不给任何资料时，模型回答与学说标准答案的接近程度。它近似反映“训练语料里有没有这套学说”。
- **grounded 对齐率**：注入知识库后的接近程度，反映“知识资产作为外部记忆”的质量上限。
- **两者的差（提升）**：就是这套知识资产对模型回答的实际增益，也是“被调用”价值的直接证据。
- **术语数**：回答中出现了多少个学说术语，反映词汇渗透度；只看提及会高估，因为模型会复述问题。

> 说明：评分基于字面覆盖，不等于事实正确；它适合看趋势与条件对比，不适合给单条回答打分。
"""
    md_path = out / f"probe-{stamp}.md"
    md_path.write_text(md, encoding="utf-8")
    (out / "latest.md").write_text(md, encoding="utf-8")
    (out / "latest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "summary": s}
