"""知识库变更工具：写 kb.json 的同时留痕。

三条规则：

1. 任何写操作都必须带依据（`--basis`：文稿名、章节，或「作者口述」），否则拒绝执行；
2. 若本次变更让术语 / 问答 / 关系的数量减少，而没给理由（`--reason`），拒绝执行且不落盘；
3. 每次成功写入，追加一行到 `docs/变更记录/kb.jsonl`（可随仓库版本管理）。

字段：时间、对象（term / faq / relation）、动作（add / update / delete）、改前、改后、理由、依据、
以及变更前后的计数，便于逐条回查。
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

KB_REL = Path("data") / "kb.json"
PACKAGE_KB_REL = Path("mcai") / "data" / "default" / "data" / "kb.json"
LOG_REL = Path("docs") / "变更记录" / "kb.jsonl"

KINDS = ("term", "faq", "relation")
ACTIONS = ("add", "update", "delete")


class ChangeError(Exception):
    """拒绝执行（未落盘）。"""


def log_path(root: str | Path) -> Path:
    return Path(root) / LOG_REL


def counts(payload: dict) -> dict:
    concepts = payload.get("concepts") or []
    return {
        "terms": len(concepts),
        "faqs": len(payload.get("faqs") or []),
        "relations": sum(len(c.get("relations") or []) for c in concepts),
    }


def _load(root: Path) -> dict:
    path = root / KB_REL
    if not path.exists():
        raise ChangeError(f"未找到知识库 {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(root: Path, payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    (root / KB_REL).write_text(text, encoding="utf-8")
    pkg = root / PACKAGE_KB_REL
    if pkg.exists():
        pkg.write_text(text, encoding="utf-8")


def _append(root: Path, entry: dict) -> Path:
    path = log_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


def _refresh_stats(payload: dict) -> None:
    stats = (payload.get("meta") or {}).setdefault("stats", {})
    c = counts(payload)
    stats["terms"] = stats["concepts"] = c["terms"]
    stats["faqs"] = c["faqs"]
    stats["relations"] = c["relations"]
    stats["evidence"] = sum(len(x.get("evidence") or []) for x in payload.get("concepts") or [])


def _slug(term: str) -> str:
    ascii_slug = "".join(ch.lower() if ch.isalnum() and ch.isascii() else "-" for ch in term).strip("-")
    ascii_slug = "-".join(p for p in ascii_slug.split("-") if p)
    return ascii_slug or f"term-{abs(hash(term)) % 100000:05d}"


def _concept(payload: dict, key: str) -> dict:
    for c in payload.get("concepts") or []:
        if key in (c.get("term"), c.get("id"), c.get("slug")):
            return c
    raise ChangeError(f"未找到术语「{key}」")


def _faq(payload: dict, key: str) -> dict:
    for f in payload.get("faqs") or []:
        if key in (f.get("question"), f.get("id")):
            return f
    raise ChangeError(f"未找到问答「{key}」")


def _edge(key: str) -> tuple[str, str]:
    for sep in ("->", "→", "=>"):
        if sep in key:
            src, dst = key.split(sep, 1)
            if src.strip() and dst.strip():
                return src.strip(), dst.strip()
    raise ChangeError(f"关系键「{key}」格式应为「源术语->目标术语」")


def _relation(payload: dict, src: str, dst: str) -> tuple[dict, dict]:
    c = _concept(payload, src)
    for r in c.get("relations") or []:
        if dst in (r.get("target"), r.get("target_id")):
            return c, r
    raise ChangeError(f"未找到关系「{src}->{dst}」")


def apply(root: str | Path, *, kind: str, action: str, key: str, field: str | None = None,
          value: str | None = None, reason: str = "", basis: str = "",
          category: str = "", en: str = "", dry_run: bool = False) -> dict:
    """执行一次知识库变更；返回落盘后的记录（dry_run 时不写）。"""
    root = Path(root).resolve()
    if kind not in KINDS:
        raise ChangeError(f"未知对象类型「{kind}」（可选：{'/'.join(KINDS)}）")
    if action not in ACTIONS:
        raise ChangeError(f"未知动作「{action}」（可选：{'/'.join(ACTIONS)}）")
    if not basis.strip():
        raise ChangeError("缺少依据：请用 --basis 写明文稿名/章节，或写「作者口述」；未落盘。")
    if action != "delete" and value is None and kind != "term":
        raise ChangeError("缺少新内容：请用 --value 提供。")

    payload = _load(root)
    before_counts = counts(payload)
    before: object = None
    after: object = None
    used_field = field or {"term": "definition", "faq": "answer", "relation": "type"}[kind]

    if kind == "term":
        if action == "update":
            c = _concept(payload, key)
            if used_field not in ("definition", "short_definition", "category", "en"):
                raise ChangeError("术语可改字段：definition / short_definition / category / en")
            before, after = c.get(used_field), value
            c[used_field] = value
        elif action == "add":
            if not value:
                raise ChangeError("新增术语需要 --value 作为定义")
            if any(key in (c.get("term"), c.get("id"), c.get("slug")) for c in payload.get("concepts") or []):
                raise ChangeError(f"术语「{key}」已存在")
            slug = _slug(key)
            concept = {"id": slug, "term": key, "slug": slug, "en": en,
                       "category": category or "元意识体系", "definition": value,
                       "short_definition": value[:60], "kind": "core", "parent": "",
                       "parent_id": "", "disambiguation": "", "status": "ok", "issues": [],
                       "sources": [], "variants": [], "edition_variants": [], "evidence": [],
                       "relations": []}
            payload["concepts"].append(concept)
            before, after = None, {"term": key, "definition": value}
        else:  # delete
            c = _concept(payload, key)
            before = {"term": c.get("term"), "definition": c.get("definition", ""),
                      "category": c.get("category", ""), "relations": len(c.get("relations") or [])}
            payload["concepts"].remove(c)
            term = before["term"]
            for other in payload["concepts"]:
                other["relations"] = [r for r in (other.get("relations") or [])
                                      if r.get("target") != term]
            after = None
    elif kind == "faq":
        if action == "update":
            f = _faq(payload, key)
            if used_field not in ("answer", "question", "short_answer", "confidence"):
                raise ChangeError("问答可改字段：answer / question / short_answer / confidence")
            before, after = f.get(used_field), value
            f[used_field] = value
        elif action == "add":
            if not value:
                raise ChangeError("新增问答需要 --value 作为答案")
            if any(f.get("question") == key for f in payload.get("faqs") or []):
                raise ChangeError(f"问答「{key}」已存在")
            payload["faqs"].append({"id": _slug(key)[:24], "question": key, "short_answer": value[:80],
                                    "answer": value, "kind": "curated", "campaign": False,
                                    "related": [], "source_terms": [], "confidence": "medium"})
            before, after = None, {"question": key, "answer": value}
        else:
            f = _faq(payload, key)
            before = {"question": f.get("question"), "answer": f.get("answer", "")}
            payload["faqs"].remove(f)
            after = None
    else:  # relation
        src, dst = _edge(key)
        if action == "delete":
            c, r = _relation(payload, src, dst)
            before = {"from": src, "to": dst, "type": r.get("type"), "tier": r.get("tier")}
            c["relations"].remove(r)
            after = None
        elif action == "add":
            c = _concept(payload, src)
            _concept(payload, dst)
            if any(dst in (r.get("target"), r.get("target_id")) for r in c.get("relations") or []):
                raise ChangeError(f"关系「{src}->{dst}」已存在")
            if not value:
                raise ChangeError("新增关系需要 --value 指定关系类型")
            c.setdefault("relations", []).append({"target": dst, "target_id": "",
                                                  "type": value, "tier": "core", "evidence": ""})
            before, after = None, {"from": src, "to": dst, "type": value}
        else:
            c, r = _relation(payload, src, dst)
            before, after = r.get(used_field), value
            r[used_field] = value

    after_counts = counts(payload)
    decreased = [f"{label} {before_counts[k]}→{after_counts[k]}"
                 for k, label in (("terms", "术语"), ("faqs", "问答"), ("relations", "关系"))
                 if after_counts[k] < before_counts[k]]
    if decreased and not reason.strip():
        raise ChangeError(
            "拒绝：本次变更会减少数量（" + "、".join(decreased) +
            "），必须提供理由（--reason）；知识库未改动。"
        )

    entry = {
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
        "kind": kind,
        "action": action,
        "key": key,
        "field": used_field if action == "update" else None,
        "before": before,
        "after": after,
        "reason": reason.strip(),
        "basis": basis.strip(),
        "counts_before": before_counts,
        "counts_after": after_counts,
        "applied": not dry_run,
    }
    if dry_run:
        return entry

    _refresh_stats(payload)
    entry["counts_after"] = counts(payload)
    _dump(root, payload)
    path = _append(root, entry)
    entry["log"] = str(path)
    return entry
