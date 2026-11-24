"""构建流水线：知识库 → 静态站 / 数据集 / 接口产物。

两种模式：

- 默认（`mcai build`）：**只从 data/kb.json 生成站点、数据集与接口产物**，
  绝不写回 kb.json，也不写 `mcai/data/default/data/kb.json`。
  知识库是唯一权威源，手改内容不会因为构建被冲掉。
- 显式重建（`mcai build --rebuild-from-corpus`）：从语料重新抽取并覆盖知识库，
  运行前打印醒目警告；这是唯一会写 kb.json 的构建路径。
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from . import dashboard, dataset, site
from .corpus import load_corpus, load_config
from .disambig import load as load_disambig
from .extract import Concept, Faq, KnowledgeBase, Source, build

KB_REL = Path("data") / "kb.json"
PACKAGE_KB_REL = Path("mcai") / "data" / "default" / "data" / "kb.json"


def kb_path(root: str | Path) -> Path:
    return Path(root) / KB_REL


def package_kb_path(root: str | Path) -> Path:
    return Path(root) / PACKAGE_KB_REL


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


def kb_from_payload(payload: dict) -> KnowledgeBase:
    """把 data/kb.json 的 JSON 还原成可供站点/数据集使用的 KnowledgeBase（只读，不落盘）。"""
    meta = payload.get("meta") or {}
    concepts = []
    for c in payload.get("concepts") or []:
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
    for f in payload.get("faqs") or []:
        data = dict(f)
        data.pop("short_answer", None)
        faqs.append(Faq(**data))

    return KnowledgeBase(
        project=meta.get("project") or {},
        concepts=concepts,
        faqs=faqs,
        documents=meta.get("documents") or [],
        stats=meta.get("stats") or {},
        built_at=meta.get("built_at", ""),
        copyright=meta.get("copyright"),
    )


def load_kb_object(root: str | Path) -> KnowledgeBase:
    """读取权威知识库；缺失时直接报错，不隐式重建（避免覆盖手改内容）。"""
    path = kb_path(root)
    if not path.exists():
        raise FileNotFoundError(
            f"未找到知识库 {path}。知识库是唯一权威源，不会被构建自动生成；"
            "如确需从语料重建，请显式运行 `mcai build --rebuild-from-corpus`。"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return kb_from_payload(payload)


def _sync_package_copy(root: Path, kb) -> bool:
    """把知识库同步到包内副本（仅显式重建时调用）。"""
    target = package_kb_path(root)
    if not target.exists():
        return False
    target.write_text(json.dumps(kb.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def _warn_overwrite(root: Path) -> None:
    print("=" * 64, file=sys.stderr)
    print("[WARN] 正在从语料重建知识库（--rebuild-from-corpus）", file=sys.stderr)
    print(f"    将覆盖：{kb_path(root)}", file=sys.stderr)
    print("    并覆盖包内副本：mcai/data/default/data/kb.json（如存在）", file=sys.stderr)
    print("    手改过的定义/问答/关系会被语料抽取结果替换，且不留痕。", file=sys.stderr)
    print("    只想更新站点/数据集请直接运行 `mcai build`（默认不写知识库）。", file=sys.stderr)
    print("=" * 64, file=sys.stderr)


def build_from_corpus(root: str | Path, *, write: bool = True) -> KnowledgeBase:
    """从语料抽取知识库；write=False 时只返回内存对象（用于漂移检测）。"""
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
    if write:
        kb.save(kb_path(root))
        _record_versions(root, kb)
        _sync_package_copy(root, kb)
    return kb


def peek_from_corpus(root: str | Path) -> KnowledgeBase:
    """只读抽取：用于对比语料与知识库的差异，不写任何文件。"""
    return build_from_corpus(root, write=False)


def _write_artifacts(root: Path, kb) -> tuple[int, list]:
    pages = site.build_site(kb, root / "dist")
    files = dataset.export(kb, root / "dist" / "dataset")
    key_file = root / "data" / "indexnow-key.txt"
    if key_file.exists():
        key = key_file.read_text(encoding="utf-8").strip()
        if key:
            (root / "dist" / f"{key}.txt").write_text(key, encoding="utf-8")
    try:
        dashboard.render(root)
    except Exception:  # noqa: BLE001 - 看板失败不影响构建
        pass
    return pages["pages"], files


def _result(kb, pages: int, files: list, *, source: str) -> dict:
    return {
        "ok": True,
        "source": source,
        "concepts": kb.stats.get("concepts", len(kb.concepts)),
        "faqs": kb.stats.get("faqs", len(kb.faqs)),
        "relations": kb.stats.get("relations", 0),
        "pages": pages,
        "dataset": files,
        "built_at": kb.built_at,
        "conflicts": [c.term for c in kb.concepts if c.status == "conflict"],
        "coverage_missing": (kb.stats.get("coverage") or {}).get("missing", []),
    }


def rebuild(root: str | Path, *, from_corpus: bool = False) -> dict:
    """构建产物。

    from_corpus=False（默认）：只从 data/kb.json 生成站点/数据集，不写知识库。
    from_corpus=True：从语料重建并覆盖知识库（显式开关，运行前有警告）。
    """
    root = Path(root).resolve()
    if from_corpus:
        _warn_overwrite(root)
        kb = build_from_corpus(root, write=True)
        source = "corpus"
    else:
        kb = load_kb_object(root)
        source = "kb"
    pages, files = _write_artifacts(root, kb)
    return _result(kb, pages, files, source=source)


def load_kb(root: str | Path) -> dict:
    path = kb_path(root)
    if not path.exists():
        raise FileNotFoundError(
            f"未找到知识库 {path}；请先放入知识库，或显式运行 `mcai build --rebuild-from-corpus`。"
        )
    return json.loads(path.read_text(encoding="utf-8"))
