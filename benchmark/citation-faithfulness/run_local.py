# -*- coding: utf-8 -*-
"""本地基线：用我们的知识引擎回答评测集，生成 predictions.jsonl。

用法：
    python benchmark/citation-faithfulness/run_local.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from mcai import knowledge  # noqa: E402

ITEMS = ROOT / "benchmark" / "citation-faithfulness" / "items.jsonl"
OUT = ROOT / "benchmark" / "citation-faithfulness" / "predictions-local.jsonl"


def main():
    kb = knowledge.load(str(ROOT))
    rows = []
    for line in ITEMS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        r = kb.answer(item["question"])
        rows.append({
            "id": item["id"],
            "type": r.get("type", ""),
            "answer": r.get("answer", ""),
            "citations": r.get("citations", []),
            "confidence": r.get("confidence", ""),
        })
    with OUT.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("answered", len(rows), "->", OUT)


if __name__ == "__main__":
    main()
