# -*- coding: utf-8 -*-
"""通用引文验证器：检查知识包中的每条引文能否在语料中定位并逐字命中。

输入格式（简单、与框架无关）：

kb.json
    {
      "concepts": [
        {"term": "...", "sources": [
          {"doc_id": "doc1", "location": "p1", "quote": "...",
           "char_start": 10, "char_end": 30, "origin": "corpus"}
        ]}
      ]
    }

corpus.jsonl（每行一个文本块）
    {"doc_id": "doc1", "location": "p1", "text": "..."}

用法：
    python -m mcai.verify --kb data/kb.json --corpus build/corpus.jsonl
    python -m mcai.verify --kb data/kb.json --corpus-config config/corpus.json
    python -m mcai.verify ... --json report.json

退出码：0 全部逐字命中；1 存在问题（可用于 CI）。
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    return re.sub(r"\s+", "", text)


def load_blocks(path: Path):
    """支持两种语料：corpus.jsonl，或旧版 corpus.json（借助 mcai.corpus）。"""
    if path.is_dir():
        candidate = path / "corpus.jsonl"
        if candidate.exists():
            path = candidate

    blocks = {}
    if path.suffix == ".jsonl":
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            blocks[(row["doc_id"], row["location"])] = row.get("text", "")
        return blocks

    if path.suffix == ".json":
        from mcai.corpus import load_corpus
        corpus = load_corpus(str(path))
        for doc in corpus.documents:
            for block in doc.blocks:
                blocks[(block.doc_id, block.location)] = block.text
        return blocks

    raise SystemExit(f"无法识别的语料格式：{path}")


def verify(kb_path: Path, corpus_path: Path):
    kb = json.loads(kb_path.read_text(encoding="utf-8"))
    blocks = load_blocks(corpus_path)

    stats = {
        "total": 0, "curated": 0, "located": 0,
        "exact": 0, "normalized": 0, "offset_ok": 0,
    }
    problems = []

    for c in kb.get("concepts", []):
        term = c.get("term", c.get("id", "?"))
        for s in c.get("sources", []):
            stats["total"] += 1
            if s.get("origin") == "curated":
                stats["curated"] += 1
                continue
            key = (s.get("doc_id"), s.get("location"))
            text = blocks.get(key)
            if text is None:
                problems.append({"term": term, "doc_id": key[0], "location": key[1],
                                 "kind": "location_not_found"})
                continue
            stats["located"] += 1
            quote = s.get("quote", "")
            if quote and quote in text:
                stats["exact"] += 1
                start, end = s.get("char_start", -1), s.get("char_end", -1)
                if start is not None and start >= 0 and text[start:end] == quote:
                    stats["offset_ok"] += 1
                else:
                    problems.append({"term": term, "doc_id": key[0], "location": key[1],
                                     "kind": "offset_mismatch"})
            elif quote and norm(quote) in norm(text):
                stats["normalized"] += 1
                problems.append({"term": term, "doc_id": key[0], "location": key[1],
                                 "kind": "normalized_match_only"})
            else:
                problems.append({"term": term, "doc_id": key[0], "location": key[1],
                                 "kind": "quote_not_in_block"})

    corpus_total = stats["total"] - stats["curated"]
    stats["corpus_total"] = corpus_total
    ok = corpus_total > 0 and stats["exact"] + stats["normalized"] == corpus_total
    report = {"ok": ok, "stats": stats, "problems": problems}
    return report


def render_text(report):
    s = report["stats"]
    total = s["corpus_total"]

    def pct(n):
        return f"{n / total:.1%}" if total else "n/a"

    lines = [
        f"来源总数: {s['total']}（语料 {total} / 人工 {s['curated']}）",
        f"可定位: {s['located']} ({pct(s['located'])})",
        f"逐字命中: {s['exact']} ({pct(s['exact'])})",
        f"归一化命中: {s['normalized']}",
        f"字符区间一致: {s['offset_ok']} ({pct(s['offset_ok'])})",
    ]
    if report["problems"]:
        lines.append("")
        lines.append(f"问题（{len(report['problems'])} 条，前 10 条）：")
        for p in report["problems"][:10]:
            lines.append(f"  - {p['term']} | {p['doc_id']} | {p['location']} | {p['kind']}")
    lines.append("")
    lines.append("结论: " + ("通过" if report["ok"] else "存在问题"))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mcai.verify", description="通用引文验证器")
    ap.add_argument("--kb", required=True, help="知识包 kb.json 路径")
    ap.add_argument("--corpus", help="corpus.jsonl 路径或目录")
    ap.add_argument("--corpus-config", help="旧版 config/corpus.json 路径")
    ap.add_argument("--json", help="把报告写入 JSON 文件")
    args = ap.parse_args(argv)

    if not args.corpus and not args.corpus_config:
        ap.error("需要 --corpus 或 --corpus-config")
    corpus = Path(args.corpus) if args.corpus else Path(args.corpus_config)
    report = verify(Path(args.kb), corpus)
    print(render_text(report))
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n报告已写入 {args.json}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
