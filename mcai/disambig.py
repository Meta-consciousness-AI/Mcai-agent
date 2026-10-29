"""阶段性消歧层。

设计原则：
- 否定句（“它不是什么”）永远不进入 definition，也不进入概念首屏；
- 只在特定阶段、以独立区块 / 独立问答 / schema 的 disambiguatingDescription 出现；
- 整个层可通过 enabled=false 一次性关闭，词条回到中性表述。
"""
from __future__ import annotations

import json
from pathlib import Path


class Disambiguation:
    def __init__(self, data: dict | None = None):
        data = data or {}
        self.campaign = data.get("campaign", {})
        self.items = {item["term"]: item for item in data.get("items", []) if item.get("term")}
        self.enabled = bool(self.campaign.get("enabled"))
        self.scope = set(self.campaign.get("scope", []))

    @property
    def active(self) -> bool:
        return self.enabled and bool(self.items)

    @property
    def status(self) -> dict:
        return {
            "enabled": self.enabled,
            "campaign": self.campaign.get("name", ""),
            "start": self.campaign.get("start", ""),
            "review_after": self.campaign.get("review_after", ""),
            "items": len(self.items),
            "note": self.campaign.get("note", ""),
        }

    def note_for(self, term: str) -> str:
        if not self.active or "schema" not in self.scope:
            return ""
        item = self.items.get(term)
        return item.get("one_line", "") if item else ""

    def page_block(self, term: str) -> dict | None:
        if not self.active or "concept_page" not in self.scope:
            return None
        return self.items.get(term)

    def faq_entries(self) -> list[dict]:
        if not self.active or "faq" not in self.scope:
            return []
        out = []
        for term, item in self.items.items():
            other = item.get("confused_with", "").strip()
            if not other:
                continue
            out.append({
                "term": term,
                "question": f"「{term}」是{other}吗？",
                "answer": f"不是。{item.get('one_line', '')}",
                "reason": item.get("reason", ""),
            })
        return out


def load(path: str | Path | None) -> Disambiguation:
    if not path:
        return Disambiguation()
    p = Path(path)
    if not p.exists():
        return Disambiguation()
    return Disambiguation(json.loads(p.read_text(encoding="utf-8-sig")))
