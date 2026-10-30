"""概念抽取：从语料段落中抽取「术语：定义」，合并多来源、检测冲突、构建关系与 FAQ。"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import text as T
from .corpus import Block, Corpus

TERM_RE = re.compile(r"^\s*([^：:，。；、！？()（）《》\"']{2,16})\s*(?:[：:]|——|—|＝|=)\s*(.+)$")
_BAD_TERM = re.compile(r"^(\d+|[A-Za-z]{1,2}|[一二三四五六七八九十]+[、.．]?)")
_ALIAS_PATTERNS = [
    re.compile(r"[，,]\s*(?:又称|也称|亦称|简称|俗称|又名)([\u4e00-\u9fa5A-Za-z]{2,12})"),
    re.compile(r"(?:也就是|即|即所谓)([\u4e00-\u9fa5]{2,10})"),
    re.compile(r"叫([\u4e00-\u9fa5]{2,8})(?:的|，|。|$|（)"),
]
_STOP_PREFIX = ("核心逻辑", "行动指南", "目标效果", "示例", "例子", "应对", "注", "说明",
                "结论", "总结", "背景", "风险", "策略", "方法", "步骤", "定义", "概念")


@dataclass
class Source:
    doc_id: str
    doc_title: str
    section: str
    location: str
    quote: str
    priority: int
    char_start: int = -1
    char_end: int = -1
    origin: str = "corpus"


@dataclass
class Variant:
    doc_id: str
    doc_title: str
    definition: str
    similarity: float


@dataclass
class Concept:
    term: str
    slug: str
    definition: str
    category: str = "其他"
    en: str = ""
    aliases: list[str] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)
    variants: list[Variant] = field(default_factory=list)
    relations: list[dict] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
    kind: str = "core"          # core | derived
    parent: str = ""            # 衍生术语的父概念
    parent_id: str = ""
    disambiguation: str = ""    # 阶段性消歧句（不进入 definition）
    tags: list[str] = field(default_factory=list)
    status: str = "ok"
    issues: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.slug

    @property
    def short_definition(self) -> str:
        parts = T.sentences(self.definition)
        if not parts:
            return T.clean(self.definition)[:90]
        acc = parts[0]
        i = 1
        # 避免以分号、逗号结尾的碎片开头，最多拼接三段
        while i < len(parts) and i < 3 and (len(acc) < 24 or acc.endswith(("；", ";", "，", ","))):
            acc += parts[i]
            i += 1
        if len(acc) > 100:
            acc = acc[:100].rstrip("，,、；") + "……"
        return acc

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "term": self.term,
            "slug": self.slug,
            "en": self.en,
            "category": self.category,
            "definition": self.definition,
            "short_definition": self.short_definition,
            "aliases": self.aliases,
            "tags": self.tags,
            "kind": self.kind,
            "parent": self.parent,
            "parent_id": self.parent_id,
            "disambiguation": self.disambiguation,
            "status": self.status,
            "issues": self.issues,
            "sources": [s.__dict__ for s in self.sources],
            "variants": [v.__dict__ for v in self.variants],
            "evidence": self.evidence,
            "relations": self.relations,
        }


@dataclass
class Faq:
    id: str
    question: str
    answer: str
    kind: str
    related: list[str] = field(default_factory=list)
    source_terms: list[str] = field(default_factory=list)
    confidence: str = "medium"
    campaign: bool = False

    @property
    def short_answer(self) -> str:
        return T.first_sentence(self.answer, 70)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
            "short_answer": self.short_answer,
            "answer": self.answer,
            "kind": self.kind,
            "campaign": self.campaign,
            "related": self.related,
            "source_terms": self.source_terms,
            "confidence": self.confidence,
        }


@dataclass
class KnowledgeBase:
    project: dict
    concepts: list[Concept]
    faqs: list[Faq]
    documents: list[dict]
    stats: dict
    built_at: str

    @property
    def by_term(self) -> dict[str, Concept]:
        return {c.term: c for c in self.concepts}

    def to_dict(self) -> dict:
        return {
            "meta": {
                "project": self.project,
                "built_at": self.built_at,
                "documents": self.documents,
                "stats": self.stats,
            },
            "concepts": [c.to_dict() for c in self.concepts],
            "faqs": [f.to_dict() for f in self.faqs],
        }

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def _reject_term(term: str, blacklist: list[str], curated: dict) -> bool:
    term = term.strip().strip("—-－ ")
    if not (2 <= len(term) <= 16):
        return True
    if term in blacklist or term in curated.get("drop_terms", []):
        return True
    if term in curated.get("excluded_entities", []):
        return True
    if any(term.startswith(p) for p in _STOP_PREFIX):
        return True
    if term in ("表格", "目录", "引言", "注释", "参考", "文献"):
        return True
    if _BAD_TERM.match(term):
        return True
    if re.search(r"\d", term):
        return True
    allowed = {t for members in curated.get("categories", {}).values() for t in members}
    if term not in allowed:
        if "的" in term or any(k in term for k in ("可能", "是否", "我们", "及其", "具有")):
            return True
    return False


def _collect_blocks(corpus: Corpus, blacklist: list[str], curated: dict) -> list[tuple[str, str, Block]]:
    """只从术语/模型类文档抽取定义；叙事与运营文档仅作为使用证据。"""
    allowed = {"glossary", "model"}
    alias_map = curated.get("term_aliases", {})
    hits: list[tuple[str, str, Block]] = []
    for doc in corpus.documents:
        if doc.kind not in allowed:
            continue
        for block in doc.blocks:
            if not block.is_term_line:
                continue
            m = TERM_RE.match(block.text)
            if not m:
                continue
            raw_term = m.group(1).strip().strip("—-－ ")
            definition = T.clean(m.group(2))
            if raw_term in alias_map:
                term = alias_map[raw_term]
            else:
                if _reject_term(raw_term, blacklist, curated):
                    continue
                term = raw_term
            if any(k in term for k in ("可能", "是否", "我们", "及其", "具有")):
                continue
            if len(term) > 16 or len(definition) < 8:
                continue
            if definition.endswith("？") or definition.endswith("?"):
                continue
            hits.append((term, definition, block))
    return hits


def _alias_candidates(term: str, definition: str, known_terms: set[str]) -> list[str]:
    """只接受「已知术语」作为别名，避免把「其他文化中的」之类误抓进来。"""
    out: list[str] = []
    if "与" in term and len(term) <= 14:
        parts = [p for p in term.split("与") if len(p) >= 2]
        if len(parts) == 2 and all(p in known_terms for p in parts):
            out.extend(parts)
    for pattern in _ALIAS_PATTERNS:
        for m in pattern.finditer(definition):
            candidate = m.group(1).strip()
            if candidate != term and candidate in known_terms:
                out.append(candidate)
    return out


def _resolve_slug(term: str, slugs: dict[str, str], used: set[str]) -> str:
    base = slugs.get(term) or f"c-{T.md5_short(term)}"
    slug, n = base, 2
    while slug in used:
        slug = f"{base}-{n}"
        n += 1
    used.add(slug)
    return slug


def _category_for(term: str, block: Block, curated: dict) -> str:
    for name, members in curated.get("categories", {}).items():
        if term in members:
            return name
    section = block.section[-1] if block.section else ""
    if "元子" in section:
        return "元子社会"
    if "本体" in section:
        return "本体论模型"
    if "序生" in section:
        return "序生体系"
    return {
        "terms": "元意识体系",
        "minimal": "元意识体系",
        "noumenon": "本体论模型",
        "metabeing": "元子社会",
    }.get(block.doc_id, "元意识体系")


def _extra_hits(corpus: Corpus, curated: dict) -> list[tuple[str, str, Block]]:
    """编辑层补充概念：以人工确认的定义作为主分支（优先级最高）。"""
    hits: list[tuple[str, str, Block]] = []
    docs = {d.doc_id: d for d in corpus.documents}
    for item in curated.get("extra_concepts", []):
        doc = docs.get(item.get("doc_id", ""))
        if doc is None:
            continue
        block = Block(
            doc_id=doc.doc_id,
            doc_title=doc.title,
            order=-1,
            text=item["quote"],
            style="Curated",
            section=(doc.title, item.get("category", "")),
            location="curated",
        )
        hits.append((item["term"], item["definition"], block))
    return hits


def build(corpus: Corpus, curated: dict, overrides: dict | None = None,
          disambig=None) -> KnowledgeBase:
    overrides = overrides or {}
    hits = _collect_blocks(corpus, corpus.term_blacklist, curated)
    hits.extend(_extra_hits(corpus, curated))
    hits.extend(_override_hits(corpus, overrides))

    grouped: dict[str, list[tuple[str, Block]]] = {}
    for term, definition, block in hits:
        grouped.setdefault(term, []).append((definition, block))

    used_slugs: set[str] = set()
    known_terms = set(grouped) | {
        t for members in curated.get("categories", {}).values() for t in members
    }
    overridden = {
        term for term, patch in overrides.items()
        if isinstance(patch, dict) and (patch.get("definition") or "").strip()
    }
    extra_meta = {
        item["term"]: item for item in curated.get("extra_concepts", [])
        if isinstance(item, dict) and item.get("term")
    }
    concepts: list[Concept] = []
    for term, entries in grouped.items():
        entries.sort(key=lambda e: -_priority(e[1]))
        canonical_def, canonical_block = entries[0]
        concept = Concept(
            term=term,
            slug=_resolve_slug(term, corpus.slugs, used_slugs),
            definition=canonical_def,
            category=_category_for(term, canonical_block, curated),
            en=curated.get("english", {}).get(term, ""),
        )

        for definition, block in entries:
            idx = block.text.find(definition)
            if idx < 0:
                idx = block.text.find(definition.strip())
            concept.sources.append(
                Source(
                    doc_id=block.doc_id,
                    doc_title=block.doc_title,
                    section=block.section[-1] if block.section else "",
                    location=block.location,
                    quote=definition,
                    priority=_priority(block),
                    char_start=idx,
                    char_end=(idx + len(definition)) if idx >= 0 else -1,
                    origin=("curated" if block.location == "curated" else "corpus"),
                )
            )

        for definition, block in entries[1:]:
            sim = T.similarity(canonical_def, definition)
            shorter, longer = sorted((canonical_def, definition), key=len)
            # 一条是另一条的前缀/节选时不算冲突（常见于 Word 手动换行被截断）
            if T.normalize(shorter) in T.normalize(longer) or T.coverage(shorter, longer) >= 0.75:
                continue
            length_ratio = min(len(definition), len(canonical_def)) / max(len(definition), len(canonical_def))
            if sim < 0.6 and length_ratio < 0.8 and len(definition) >= 24:
                concept.variants.append(
                    Variant(block.doc_id, block.doc_title, definition, round(sim, 3))
                )

        canonical_terms = set(grouped)
        aliases = list(curated.get("aliases", {}).get(term, []))
        for definition, _ in entries:
            for candidate in _alias_candidates(term, definition, known_terms):
                # 别名不能是另一个概念的正名（否则会互相抢占）
                if candidate in canonical_terms and candidate != term:
                    continue
                if candidate not in aliases:
                    aliases.append(candidate)
        concept.aliases = [a for a in aliases if a and a != term]

        patch = overrides.get(term) if isinstance(overrides.get(term), dict) else {}
        meta = extra_meta.get(term) or {}
        if meta.get("kind") == "derived":
            concept.kind = "derived"
            concept.parent = meta.get("parent", "")
        if patch:
            if patch.get("en"):
                concept.en = patch["en"]
            if patch.get("category"):
                concept.category = patch["category"]
            for extra_alias in patch.get("aliases", []) or []:
                if extra_alias not in concept.aliases:
                    concept.aliases.append(extra_alias)

        if term in overridden:
            concept.variants = []
            concept.issues = [i for i in concept.issues if "差异较大的定义" not in i]

        if concept.variants:
            concept.status = "conflict"
            concept.issues.append(f"存在 {len(concept.variants)} 个差异较大的定义版本，需人工裁定")
        if len(concept.definition) < 12:
            concept.status = "thin" if concept.status == "ok" else concept.status
            concept.issues.append("定义过短，可能不足以被 AI 直接引用")
        concepts.append(concept)

    concepts.sort(key=lambda c: (c.category, -len(c.definition)))
    by_term_final = {c.term: c for c in concepts}
    for concept in concepts:
        if concept.parent and concept.parent in by_term_final:
            concept.parent_id = by_term_final[concept.parent].id

    _link_relations(concepts, curated)
    evidence_count = _attach_evidence(concepts, corpus, curated)
    if disambig is not None and getattr(disambig, "active", False):
        for concept in concepts:
            note = disambig.note_for(concept.term)
            if note:
                concept.disambiguation = note
    faqs = _build_faq(concepts, curated, disambig)

    documents = [
        {"id": d.doc_id, "title": d.title, "path": d.path, "kind": d.kind,
         "priority": d.priority, "blocks": len(d.blocks), "sections": len(d.sections())}
        for d in corpus.documents
    ]
    stats = _stats(concepts, faqs, curated, corpus, evidence_count, disambig)

    return KnowledgeBase(
        project=corpus.project,
        concepts=concepts,
        faqs=faqs,
        documents=documents,
        stats=stats,
        built_at=datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    )


def _override_hits(corpus: Corpus, overrides: dict) -> list[tuple[str, str, Block]]:
    """人工审校层：overrides.json 中裁定过的定义优先级最高（高于原文与编辑层）。"""
    hits: list[tuple[str, str, Block]] = []
    docs = {d.doc_id: d for d in corpus.documents}
    doc = docs.get("minimal") or next(iter(docs.values()), None)
    if doc is None:
        return hits
    for term, patch in overrides.items():
        if term.startswith("_") or not isinstance(patch, dict):
            continue
        definition = (patch.get("definition") or "").strip()
        if not definition:
            continue
        block = Block(
            doc_id=doc.doc_id,
            doc_title=doc.title,
            order=-2,
            text=definition,
            style="Override",
            section=(doc.title, patch.get("category", "")),
            location="override",
        )
        hits.append((term, definition, block))
    return hits


def _priority(block: Block) -> int:
    if block.style == "Override":
        return 300
    if block.style == "Curated":
        return 200
    base = {"terms": 100, "minimal": 95, "noumenon": 90, "metabeing": 90,
            "progenerative": 70, "manual": 60}.get(block.doc_id, 50)
    if block.doc_title and "术语" in block.doc_title:
        base += 10
    return base


def _link_relations(concepts: list[Concept], curated: dict) -> None:
    by_term = {c.term: c for c in concepts}
    index: list[tuple[str, Concept]] = []
    for c in concepts:
        index.append((c.term, c))
        for a in c.aliases:
            if a not in by_term:
                index.append((a, c))
    index.sort(key=lambda x: -len(x[0]))

    seen: set[tuple[str, str, str]] = set()

    def add(src: Concept, dst: Concept, kind: str, evidence: str = "") -> None:
        if src is dst:
            return
        key = (src.term, dst.term, kind)
        if key in seen:
            return
        seen.add(key)
        src.relations.append({"target": dst.term, "target_id": dst.id, "type": kind, "evidence": evidence})

    for src, dst, kind in curated.get("core_loop", []):
        if src in by_term and dst in by_term:
            add(by_term[src], by_term[dst], kind)

    for item in curated.get("extra_concepts", []):
        if not isinstance(item, dict) or item.get("kind") != "derived":
            continue
        term, parent = item.get("term"), item.get("parent")
        if term in by_term and parent in by_term:
            add(by_term[term], by_term[parent], "衍生自")

    for concept in concepts:
        body = concept.definition
        for name, target in index:
            if target is concept or name == concept.term:
                continue
            if len(name) < 2 or name not in body:
                continue
            if any(name in a for a in concept.aliases):
                continue
            snippet = next((s for s in T.sentences(body) if name in s), "")
            add(concept, target, "提及", snippet[:120])

    for c in concepts:
        # 同一目标已有强关系（核心闭环/衍生自）时，不再重复保留「提及」
        strong = {r["target"] for r in c.relations if r["type"] != "提及"}
        c.relations = [r for r in c.relations if r["type"] != "提及" or r["target"] not in strong]
        c.relations.sort(key=lambda r: (r["type"] != "提及", r["target"]))


def _evidence_score(sentence: str, term: str, definition: str) -> int:
    """给候选引证打分：越像「关于该概念的论述」分越高，标题/摘要类扣分。"""
    score = 0
    pos = sentence.find(term)
    if 0 <= pos <= 12:
        score += 2
    if any(k in sentence for k in ("是指", "指的是", "称为", "所谓", "意味着", "也就是说", "本质")):
        score += 2
    sim = T.similarity(sentence, definition)
    if 0.2 <= sim <= 0.8:
        score += 1
    if sentence[:4] in ("本文首先", "本文认为", "摘要：", "关键词") or "本文" in sentence[:6]:
        score -= 3
    if sentence[:2] in ("首先", "其次", "最后", "综上", "由此") or sentence[:3] in ("最后讨", "本文梳"):
        score -= 2
    if any(k in sentence for k in ("讨论", "梳理", "辨析", "本文", "文章")):
        score -= 1
    if sentence.endswith("：") or sentence.endswith(":"):
        score -= 2
    # 标题行通常不以句末标点结尾
    if sentence[-1:] not in "。！？…”\"'":
        score -= 2
    if len(sentence) > 160:
        score -= 1
    return score


def _split_sentences(text: str) -> list[str]:
    """中文按中文标点切句；英文段落按 . ! ? 切句（否则整段会被当成一句而超长丢弃）。"""
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    if cjk <= max(2, len(text) * 0.05):
        parts = re.split(r"(?<=[.!?])\s+", text)
        return [p.strip() for p in parts if p.strip()]
    return T.sentences(text)


def _match_english(lower: str, names: list[str]) -> str | None:
    """英文术语按词边界匹配，避免 Consciousness 命中 Meta-Consciousness。"""
    for name in names:
        pattern = r"(?<![a-z-])" + re.escape(name) + r"(?![a-z-])"
        if re.search(pattern, lower):
            return name
    return None


def _attach_evidence(concepts: list[Concept], corpus: Corpus, curated: dict,
                     per_doc: int = 3, total: int = 8) -> int:
    """从「引证源」文档中摘取论述片段，只补充出处，不改动定义。"""
    docs = [d for d in corpus.documents if d.kind == "evidence"]
    if not docs:
        return 0
    titles = {d.title for d in docs}
    excluded = curated.get("excluded_entities", [])
    count = 0
    for concept in concepts:
        names = [n for n in [concept.term, *concept.aliases] if len(n) >= 2]
        english = [concept.en.lower()] if concept.en else []
        for doc in docs:
            candidates: list[tuple[int, dict]] = []
            seen: set[str] = set()
            for block in doc.blocks:
                for sentence in _split_sentences(block.text):
                    if not (16 <= len(sentence) <= 220):
                        continue
                    if sentence.strip() in titles:
                        continue
                    if any(e in sentence for e in excluded):
                        continue
                    lower = sentence.lower()
                    matched = next((n for n in names if n in sentence), None)
                    lang = "zh"
                    if not matched:
                        matched = _match_english(lower, english)
                        lang = "en"
                    if not matched:
                        continue
                    key = T.normalize(sentence)[:60]
                    if key in seen:
                        continue
                    if T.similarity(sentence, concept.definition) > 0.9:
                        continue
                    seen.add(key)
                    score = _evidence_score(sentence, matched, concept.definition)
                    if score < 0:
                        continue
                    candidates.append((score, {
                        "doc_id": doc.doc_id,
                        "doc_title": doc.title,
                        "section": block.section[-1] if block.section else "",
                        "location": block.location,
                        "quote": sentence,
                        "lang": lang,
                        "score": score,
                    }))
            candidates.sort(key=lambda item: -item[0])
            picked = [item for _, item in candidates[:per_doc]]
            concept.evidence.extend(picked)
            count += len(picked)
        zh = sorted([e for e in concept.evidence if e["lang"] == "zh"], key=lambda e: -e["score"])
        en = sorted([e for e in concept.evidence if e["lang"] == "en"], key=lambda e: -e["score"])
        concept.evidence = zh[: max(0, total - min(len(en), 2))] + en[:2]
    return count


def _build_faq(concepts: list[Concept], curated: dict, disambig=None) -> list[Faq]:
    by_term = {c.term: c for c in concepts}
    faqs: list[Faq] = []
    used: set[str] = set()

    for item in curated.get("faq_seed", []):
        q = item["question"]
        used.add(T.normalize(q))
        faqs.append(
            Faq(
                id=f"faq-{T.md5_short(q)}",
                question=q,
                answer=item["answer"],
                kind="curated",
                related=[by_term[t].id for t in item.get("related", []) if t in by_term],
                source_terms=[t for t in item.get("related", []) if t in by_term],
                confidence="high",
            )
        )

    for a, b, answer in curated.get("contrast_pairs", []):
        if a not in by_term or b not in by_term:
            continue
        q = f"{a}和{b}有什么区别？"
        if T.normalize(q) in used:
            continue
        used.add(T.normalize(q))
        faqs.append(
            Faq(
                id=f"faq-{T.md5_short(q)}",
                question=q,
                answer=answer,
                kind="contrast",
                related=[by_term[a].id, by_term[b].id],
                source_terms=[a, b],
                confidence="high",
            )
        )

    for concept in concepts:
        if concept.status == "thin":
            continue
        q = f"什么是{concept.term}？"
        if T.normalize(q) in used:
            continue
        used.add(T.normalize(q))
        answer = concept.definition
        if concept.variants:
            answer += "（注：该术语在不同文本中存在表述差异，此为主分支定义。）"
        faqs.append(
            Faq(
                id=f"faq-{T.md5_short(q)}",
                question=q,
                answer=answer,
                kind="definition",
                related=[concept.id],
                source_terms=[concept.term],
                confidence="high" if concept.status == "ok" else "medium",
            )
        )

    # 把文献引证扩成「如何理解 X」问答：定义打底 + 一条原典论述作支撑
    for concept in concepts:
        if not concept.evidence:
            continue
        best = max(concept.evidence, key=lambda e: e["score"])
        if best["score"] < 2:
            continue
        q = f"如何理解{concept.term}？"
        if T.normalize(q) in used:
            continue
        used.add(T.normalize(q))
        answer = concept.short_definition
        quote = best["quote"]
        if T.similarity(quote, answer) < 0.6:
            answer = f"{answer}《{best['doc_title']}》中进一步指出：「{quote}」"
        faqs.append(
            Faq(
                id=f"faq-{T.md5_short(q)}",
                question=q,
                answer=answer,
                kind="evidence",
                related=[concept.id],
                source_terms=[concept.term],
                confidence="high" if best["score"] >= 3 else "medium",
            )
        )

    if disambig is not None and getattr(disambig, "active", False):
        for item in disambig.faq_entries():
            q = item["question"]
            if T.normalize(q) in used:
                continue
            used.add(T.normalize(q))
            target = by_term.get(item["term"])
            faqs.append(
                Faq(
                    id=f"faq-{T.md5_short(q)}",
                    question=q,
                    answer=item["answer"],
                    kind="disambiguation",
                    related=[target.id] if target else [],
                    source_terms=[item["term"]],
                    confidence="high",
                    campaign=True,
                )
            )
    return faqs


def _stats(concepts: list[Concept], faqs: list[Faq], curated: dict, corpus: Corpus,
           evidence_count: int = 0, disambig=None) -> dict:
    by_category: dict[str, int] = {}
    by_status: dict[str, int] = {}
    concept_kind = {"core": 0, "derived": 0}
    for c in concepts:
        by_category[c.category] = by_category.get(c.category, 0) + 1
        by_status[c.status] = by_status.get(c.status, 0) + 1
        concept_kind[c.kind] = concept_kind.get(c.kind, 0) + 1

    expected = [t for members in curated.get("categories", {}).values() for t in members]
    missing = [t for t in expected if t not in {c.term for c in concepts}]
    graph_edges = sum(len(c.relations) for c in concepts)
    by_kind: dict[str, int] = {}
    for d in corpus.documents:
        by_kind[d.kind] = by_kind.get(d.kind, 0) + 1

    return {
        "concepts": len(concepts),
        "faqs": len(faqs),
        "relations": graph_edges,
        "evidence": evidence_count,
        "categories": by_category,
        "status": by_status,
        "policy": {
            "excluded_entities": curated.get("excluded_entities", []),
            "answer": curated.get("policy_answer", ""),
            "principle": curated.get("policy_principle", ""),
        },
        "concept_kind": concept_kind,
        "campaign_faqs": sum(1 for f in faqs if f.campaign),
        "disambiguation": (disambig.status if disambig is not None else {"enabled": False, "items": 0}),
        "by_kind": by_kind,
        "coverage": {
            "expected": len(expected),
            "covered": len(expected) - len(missing),
            "missing": missing,
        },
        "documents": len(corpus.documents),
        "blocks": sum(len(d.blocks) for d in corpus.documents),
        "characters": sum(len(b.text) for d in corpus.documents for b in d.blocks),
    }
