"""构建流水线：语料 → 知识库 → 静态站 → 数据集。"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import dashboard, dataset, site
from .corpus import load_corpus, load_config
from .disambig import load as load_disambig
from .extract import build


def _record_versions(root: Path, kb) -> None:
    """记录概念定义的版本变化：只追加发生变化的条目。"""
    path = root / "data" / "concept_versions.jsonl"
    last: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                last[row.get("term", "")] = row.get("hash", "")
            except json.JSONDecodeError:
                continue
    rows = []
    for c in kb.concepts:
        digest = hashlib.sha1(c.definition.encode("utf-8")).hexdigest()[:12]
        if last.get(c.term) != digest:
            rows.append({"ts": kb.built_at, "term": c.term, "hash": digest})
    if rows:
        with path.open("a", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def rebuild(root: str | Path) -> dict:
    root = Path(root).resolve()
    corpus = load_corpus(root / "config" / "corpus.json")
    curated = load_config(root / "config" / "curated.json")
    overrides_path = root / "config" / "overrides.json"
    overrides = load_config(overrides_path) if overrides_path.exists() else {}
    disambig = load_disambig(root / "config" / "disambiguation.json")
    term_path = root / "config" / "terminology.json"
    terminology = load_config(term_path) if term_path.exists() else {}
    kb = build(corpus, curated, overrides, disambig)
    kb.project["terminology"] = terminology

    kb.save(root / "data" / "kb.json")
    _record_versions(root, kb)
    pages = site.build_site(kb, root / "dist")
    files = dataset.export(kb, root / "dist" / "dataset")
    try:
        dashboard.render(root)
    except Exception:  # noqa: BLE001 - 看板失败不影响构建
        pass

    return {
        "ok": True,
        "concepts": kb.stats["concepts"],
        "faqs": kb.stats["faqs"],
        "relations": kb.stats["relations"],
        "pages": pages["pages"],
        "dataset": files,
        "built_at": kb.built_at,
        "conflicts": [c.term for c in kb.concepts if c.status == "conflict"],
        "coverage_missing": kb.stats["coverage"]["missing"],
    }


def load_kb(root: str | Path) -> dict:
    path = Path(root) / "data" / "kb.json"
    if not path.exists():
        rebuild(root)
    return json.loads(path.read_text(encoding="utf-8"))
