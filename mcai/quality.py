"""质量巡检：每次构建后自动检查知识库与站点的「硬问题」。

只报告，不改内容——术语与问答一律人工维护。
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from lxml import html


def _issue(code: str, level: str, detail: str) -> dict:
    return {"code": code, "level": level, "detail": detail}


def check_kb(kb: dict) -> list[dict]:
    issues: list[dict] = []
    concepts = kb.get("concepts", [])
    faqs = kb.get("faqs", [])
    if not concepts:
        issues.append(_issue("kb.empty", "error", "知识库没有任何概念"))
        return issues

    by_slug = {c.get("slug") for c in concepts}
    definition_map: dict[str, list[str]] = {}
    for c in concepts:
        term = c.get("term", "")
        definition = (c.get("definition") or "").strip()
        if len(definition) < 12:
            issues.append(_issue("concept.thin", "error", f"{term} 的定义过短（{len(definition)} 字）"))
        if not c.get("sources"):
            issues.append(_issue("concept.no_source", "error", f"{term} 没有定义来源"))
        if c.get("status") == "conflict":
            issues.append(_issue("concept.conflict", "error", f"{term} 存在未裁定的定义冲突"))
        slug = c.get("slug", "")
        if slug.startswith("c-"):
            issues.append(_issue("concept.slug_missing", "warn", f"{term} 未配置 URL slug（回退为 {slug}）"))
        if not c.get("en"):
            issues.append(_issue("concept.en_missing", "info", f"{term} 缺少英文名"))
        key = " ".join(definition.split())[:80]
        definition_map.setdefault(key, []).append(term)
        for rel in c.get("relations") or []:
            tid = rel.get("target_id")
            if tid and tid not in by_slug:
                issues.append(_issue("relation.dangling", "error",
                                     f"{term} 的关系指向不存在的概念 {tid}"))

    for key, terms in definition_map.items():
        if len(terms) > 1:
            issues.append(_issue("concept.duplicate_definition", "warn",
                                 "定义完全相同的术语：" + "、".join(terms)))

    seen_questions = Counter()
    for f in faqs:
        q = (f.get("question") or "").strip()
        if not q or not (f.get("answer") or "").strip():
            issues.append(_issue("faq.empty", "error", f"问答为空：{q or '(无问题)'}"))
        seen_questions[q] += 1
    for q, n in seen_questions.items():
        if n > 1:
            issues.append(_issue("faq.duplicate", "warn", f"问题重复 {n} 次：{q}"))

    stats = kb.get("meta", {}).get("stats", {})
    excluded = ((stats.get("policy") or {}).get("excluded_entities")) or []
    if excluded:
        for c in concepts:
            blob = " ".join([
                c.get("term", ""), c.get("definition", ""),
                " ".join(s.get("quote", "") for s in c.get("sources") or []),
                " ".join(e.get("quote", "") for e in c.get("evidence") or []),
            ])
            if any(e in blob for e in excluded):
                issues.append(_issue("policy.entity_leak", "error",
                                     f"{c.get('term', '')} 含被排除的人物信息"))
        for f in faqs:
            blob = (f.get("question", "") or "") + (f.get("answer", "") or "")
            if any(e in blob for e in excluded):
                issues.append(_issue("policy.entity_leak", "error",
                                     f"问答含被排除的人物信息：{f.get('question', '')[:20]}"))

    campaign = stats.get("disambiguation") or {}
    if not campaign.get("enabled") and any(f.get("campaign") for f in faqs):
        issues.append(_issue("campaign.leak", "error", "消歧层已关闭，但问答里仍有 campaign 条目"))
    missing = (stats.get("coverage") or {}).get("missing") or []
    if missing:
        issues.append(_issue("coverage.missing", "warn", "词表覆盖缺失：" + "、".join(missing[:10])))

    return issues


def check_site(dist: Path) -> list[dict]:
    issues: list[dict] = []
    pages = sorted(dist.rglob("*.html"))
    if not pages:
        return [_issue("site.empty", "error", "dist 下没有 HTML 页面")]

    missing_targets: set[str] = set()
    jsonld_errors = 0
    for page in pages:
        try:
            doc = html.parse(str(page)).getroot()
        except Exception as exc:  # noqa: BLE001
            issues.append(_issue("site.parse", "error", f"{page.name} 解析失败：{exc}"))
            continue
        if not doc.findtext(".//title"):
            issues.append(_issue("site.title", "warn", f"{page.name} 缺少 title"))
        for href in doc.xpath("//a/@href"):
            if not href.startswith("/") or href.startswith("//"):
                continue
            target = dist / href.lstrip("/")
            if href.endswith("/"):
                target = target / "index.html"
            if not target.exists() and href not in missing_targets:
                missing_targets.add(href)
                issues.append(_issue("site.dead_link", "error", f"{page.name} → {href}"))
        for block in doc.xpath('//script[@type="application/ld+json"]/text()'):
            try:
                data = json.loads(block)
                if "@context" not in data:
                    jsonld_errors += 1
            except json.JSONDecodeError:
                jsonld_errors += 1
    if jsonld_errors:
        issues.append(_issue("site.jsonld", "error", f"{jsonld_errors} 处 JSON-LD 无效"))

    for name in ("index.html", "llms.txt", "sitemap.xml", "guide.md",
                 ".well-known/mcp.json", ".well-known/agent.json", "openapi.json"):
        if not (dist / name).exists():
            issues.append(_issue("site.missing_artifact", "error", f"缺少 {name}"))
    return issues


def inspect(root: str | Path) -> dict:
    root = Path(root)
    issues: list[dict] = []
    kb_path = root / "data" / "kb.json"
    if not kb_path.exists():
        issues.append(_issue("kb.missing", "error", "data/kb.json 不存在，尚未构建"))
    else:
        try:
            issues.extend(check_kb(json.loads(kb_path.read_text(encoding="utf-8"))))
        except json.JSONDecodeError as exc:
            issues.append(_issue("kb.invalid", "error", f"kb.json 解析失败：{exc}"))
    dist = root / "dist"
    if dist.exists():
        issues.extend(check_site(dist))

    errors = [i for i in issues if i["level"] == "error"]
    warnings = [i for i in issues if i["level"] == "warn"]
    infos = [i for i in issues if i["level"] == "info"]
    result = {
        "ok": not errors,
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "errors": errors,
        "warnings": warnings,
        "infos": infos,
        "counts": {"error": len(errors), "warn": len(warnings), "info": len(infos)},
    }
    out = root / "data" / "quality.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
