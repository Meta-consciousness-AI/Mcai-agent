"""核验引文：检查 kb.json 里每条 source 是否能在语料中定位。

用法：
    python tools/verify_citations.py [--kb data/kb.json] [--config config/corpus.json]

统计分两类：
- origin=corpus：应能在语料中定位并逐字命中；
- origin=curated：人工补充定义，不参与语料核验，单独计数。

退出码：0 表示语料来源全部命中；1 表示存在缺失（可用于 CI）。
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai.corpus import load_corpus  # noqa: E402


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    return re.sub(r"\s+", "", text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", default=str(ROOT / "data" / "kb.json"))
    ap.add_argument("--config", default=str(ROOT / "config" / "corpus.json"))
    args = ap.parse_args()

    kb = json.loads(Path(args.kb).read_text(encoding="utf-8"))
    corpus = load_corpus(args.config)
    index = {}
    for doc in corpus.documents:
        for block in doc.blocks:
            index[(block.doc_id, block.location)] = block

    total = curated = located = exact = normalized = offset_ok = 0
    problems = []
    for c in kb.get("concepts", []):
        for s in c.get("sources", []):
            total += 1
            if s.get("origin") == "curated":
                curated += 1
                continue
            block = index.get((s.get("doc_id"), s.get("location")))
            if block is None:
                problems.append((c["term"], s.get("doc_id"), s.get("location"), "location_not_found"))
                continue
            located += 1
            quote = s.get("quote", "")
            if quote and quote in block.text:
                exact += 1
                start, end = s.get("char_start", -1), s.get("char_end", -1)
                if start is not None and start >= 0 and block.text[start:end] == quote:
                    offset_ok += 1
                else:
                    problems.append((c["term"], s.get("doc_id"), s.get("location"), "offset_mismatch"))
            elif quote and norm(quote) in norm(block.text):
                normalized += 1
                problems.append((c["term"], s.get("doc_id"), s.get("location"), "normalized_match_only"))
            else:
                problems.append((c["term"], s.get("doc_id"), s.get("location"), "quote_not_in_block"))

    corpus_total = total - curated
    pct = (lambda n: f"{n / corpus_total:.1%}" if corpus_total else "n/a")
    print(f"来源总数: {total}（语料 {corpus_total} / 人工 {curated}）")
    print(f"可定位: {located} ({pct(located)})")
    print(f"逐字命中: {exact} ({pct(exact)})")
    print(f"归一化命中: {normalized}")
    print(f"字符区间一致: {offset_ok} ({pct(offset_ok)})")
    if problems:
        print("\n问题（前 10 条）：")
        for p in problems[:10]:
            print("  -", " | ".join(str(x) for x in p))
    ok = corpus_total > 0 and (exact + normalized) == corpus_total
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
