# -*- coding: utf-8 -*-
"""从现有 data/kb.json 直接生成静态站点，不重新抽取语料。

用途：术语审校后只更新了 kb，不想因为 mcai build 重新抽取而覆盖修订。
用法：python tools/build_site_from_kb.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai import dataset, site  # noqa: E402
from mcai.extract import Concept, Faq, KnowledgeBase, Source  # noqa: E402


def main() -> int:
    payload = json.loads((ROOT / "data" / "kb.json").read_text(encoding="utf-8"))
    meta = payload["meta"]

    concepts = []
    for c in payload["concepts"]:
        data = dict(c)
        data.pop("id", None)
        data.pop("hidden_aliases", None)
        data.pop("short_definition", None)
        data["sources"] = [
            Source(
                doc_id=s.get("doc_id", ""),
                doc_title=s.get("doc_title", ""),
                section=s.get("section", ""),
                location=s.get("location", ""),
                quote=s.get("quote", ""),
                priority=int(s.get("priority", 60) or 60),
                char_start=int(s.get("char_start", -1) if s.get("char_start") is not None else -1),
                char_end=int(s.get("char_end", -1) if s.get("char_end") is not None else -1),
                origin=s.get("origin", "corpus"),
                edition=s.get("edition", ""),
            )
            for s in c.get("sources", [])
        ]
        concepts.append(Concept(**data))

    faqs = []
    for f in payload["faqs"]:
        data = dict(f)
        data.pop("short_answer", None)
        faqs.append(Faq(**data))

    kb = KnowledgeBase(
        project=meta["project"],
        concepts=concepts,
        faqs=faqs,
        documents=meta.get("documents", []),
        stats=meta.get("stats", {}),
        built_at=meta.get("built_at", ""),
        copyright=meta.get("copyright"),
    )
    info = site.build_site(kb, ROOT / "dist")
    from mcai import dashboard

    dataset.export(kb, ROOT / "dist" / "dataset")

    dashboard.render(ROOT)
    print(json.dumps(info, ensure_ascii=False, indent=2))
    print("version:", meta["project"].get("version"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
