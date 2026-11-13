# -*- coding: utf-8 -*-
"""评分：按层级统计引用忠实度与拒答准确率。

层级：exact / paraphrase / homonym / refusal

用法：
    python benchmark/citation-faithfulness/score.py \
        --items benchmark/citation-faithfulness/items.jsonl \
        --predictions benchmark/citation-faithfulness/predictions-local.jsonl \
        --corpus-config config/corpus.json
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from mcai.verify import load_blocks  # noqa: E402


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    return re.sub(r"\s+", "", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", default=str(ROOT / "benchmark" / "citation-faithfulness" / "items.jsonl"))
    ap.add_argument("--predictions", default=str(ROOT / "benchmark" / "citation-faithfulness" / "predictions-local.jsonl"))
    ap.add_argument("--corpus-config", default=str(ROOT / "config" / "corpus.json"))
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    items = [json.loads(l) for l in Path(args.items).read_text(encoding="utf-8").splitlines() if l.strip()]
    preds = {json.loads(l)["id"]: json.loads(l)
             for l in Path(args.predictions).read_text(encoding="utf-8").splitlines() if l.strip()}
    corpus_texts = [norm(t) for t in load_blocks(Path(args.corpus_config)).values()]

    groups = {}
    problems = []

    for item in items:
        tier = item.get("tier", "exact")
        g = groups.setdefault(tier, {
            "n": 0, "pred": 0, "matched": 0, "gold": 0, "gold_hit": 0,
            "fab": 0, "ok_items": 0, "refusal_ok": 0,
        })
        p = preds.get(item["id"])
        g["n"] += 1
        if p is None:
            problems.append({"id": item["id"], "problem": "missing_prediction"})
            continue

        if tier == "refusal":
            ans = p.get("answer") or ""
            if p.get("type") == "none" or "未找到" in ans or "没有直接命中" in ans:
                g["refusal_ok"] += 1
            else:
                problems.append({"id": item["id"], "problem": "should_refuse", "answer": ans[:60]})
            continue

        if tier == "homonym":
            cites = p.get("citations") or []
            for c in cites:
                g["pred"] += 1
                q = norm(c.get("quote"))
                if q:
                    allowed = [norm(a["quote"]) for a in item.get("allowed_sources", [])]
                    if not any(q in t for t in corpus_texts) and not any(q in a or a in q for a in allowed):
                        g["fab"] += 1
            if (p.get("answer") or "").strip() and g["fab"] == 0:
                g["ok_items"] += 1
            continue

        golds = [norm(x["quote"]) for x in item.get("gold_sources", []) if x.get("quote")]
        allowed = [norm(a["quote"]) for a in item.get("allowed_sources", []) if a.get("quote")]
        g["gold"] += len(golds)
        cites = p.get("citations") or []
        before = g["matched"]
        for c in cites:
            g["pred"] += 1
            q = norm(c.get("quote"))
            if not q:
                continue
            if not any(q in t for t in corpus_texts) and not any(q in a or a in q for a in allowed):
                g["fab"] += 1
                problems.append({"id": item["id"], "problem": "quote_not_in_corpus", "quote": (c.get("quote") or "")[:60]})
                continue
            if any(q in gq or gq in q for gq in golds) or any(q in a or a in q for a in allowed):
                g["matched"] += 1
        hit = 0
        for gq in golds:
            if any(norm(c.get("quote")) and (norm(c.get("quote")) in gq or gq in norm(c.get("quote")))
                   for c in cites):
                hit += 1
        g["gold_hit"] += hit
        if hit or g["matched"] > before:
            g["ok_items"] += 1

    def pct(a, b):
        return f"{a / b:.1%}" if b else "n/a"

    order = ["exact", "paraphrase", "homonym", "semantic", "refusal"]
    print(f"{'tier':12s} {'n':>4s} {'precision':>10s} {'recall':>8s} {'coverage':>9s} {'fabrication':>12s} {'refusal':>8s}")
    summary = {}
    for tier in order:
        g = groups.get(tier)
        if not g:
            continue
        if tier == "refusal":
            row = (g["n"], "—", "—", "—", "—", pct(g["refusal_ok"], g["n"]))
            summary[tier] = {"n": g["n"], "refusal_accuracy": g["refusal_ok"] / g["n"] if g["n"] else 0}
        elif tier == "homonym":
            row = (g["n"], "—", "—", pct(g["ok_items"], g["n"]), pct(g["fab"], g["pred"]), "—")
            summary[tier] = {"n": g["n"], "coverage": g["ok_items"] / g["n"] if g["n"] else 0,
                             "fabrication_rate": g["fab"] / g["pred"] if g["pred"] else 0}
        else:
            row = (g["n"], pct(g["matched"], g["pred"]), pct(g["gold_hit"], g["gold"]),
                   pct(g["ok_items"], g["n"]), pct(g["fab"], g["pred"]), "—")
            summary[tier] = {"n": g["n"], "precision": g["matched"] / g["pred"] if g["pred"] else 0,
                             "recall": g["gold_hit"] / g["gold"] if g["gold"] else 0,
                             "coverage": g["ok_items"] / g["n"] if g["n"] else 0,
                             "fabrication_rate": g["fab"] / g["pred"] if g["pred"] else 0}
        print(f"{tier:12s} {row[0]:>4d} {row[1]:>10s} {row[2]:>8s} {row[3]:>9s} {row[4]:>12s} {row[5]:>8s}")

    if problems:
        print(f"\n问题 {len(problems)} 条（前 10）：")
        for x in problems[:10]:
            print("  -", json.dumps(x, ensure_ascii=False))

    if args.json:
        Path(args.json).write_text(json.dumps({"summary": summary, "problems": problems},
                                              ensure_ascii=False, indent=2), encoding="utf-8")
        print("\n报告已写入", args.json)


if __name__ == "__main__":
    main()
