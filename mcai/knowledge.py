"""检索与问答内核：供 HTTP API 与 MCP 共用。

不调用大模型，全部基于词表、别名、引证与问题相似度的确定性检索，
保证回答可追溯、可复现。
"""
from __future__ import annotations

import difflib
import json
import re
import unicodedata
from pathlib import Path

from .text import clean, normalize


# 常见繁体字 → 简体字（覆盖术语与常见查询用字）
_TRAD_TO_SIMP = str.maketrans({
    "識": "识", "靈": "灵", "體": "体", "觀": "观", "測": "测", "創": "创",
    "實": "实", "現": "现", "態": "态", "時": "时", "間": "间", "網": "网",
    "場": "场", "際": "际", "學": "学", "說": "说", "義": "义", "認": "认",
    "覺": "觉", "層": "层", "級": "级", "關": "关", "係": "系", "轉": "转",
    "變": "变", "數": "数", "據": "据", "資": "资", "產": "产", "權": "权",
    "證": "证", "書": "书", "讀": "读", "語": "语", "詞": "词", "彙": "汇",
    "標": "标", "準": "准", "規": "规", "範": "范", "構": "构", "設": "设",
    "計": "计", "應": "应", "場": "场", "質": "质", "量": "量", "問": "问",
    "題": "题", "點": "点", "線": "线", "圖": "图", "譜": "谱", "鏈": "链",
})


def _norm(text: str) -> str:
    """归一化：全半角、大小写、繁简、空白与标点。"""
    t = unicodedata.normalize("NFKC", text or "").lower().translate(_TRAD_TO_SIMP)
    return re.sub(r"[\s\W_]+", "", t, flags=re.UNICODE)


def _bigrams(text: str) -> set[str]:
    s = normalize(text)
    return {s[i: i + 2] for i in range(len(s) - 1)} if len(s) > 1 else {s}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class Knowledge:
    """只读知识库视图，线程内可复用。"""

    def __init__(self, payload: dict):
        self.payload = payload
        self.meta = payload.get("meta", {})
        term_cfg = (self.meta.get("project") or {}).get("terminology") or {}
        self.terminology = term_cfg
        self._deprecated = {
            d.get("term"): d for d in (term_cfg.get("deprecated") or []) if d.get("term")
        }
        self.concepts: list[dict] = payload.get("concepts", [])
        self.faqs: list[dict] = payload.get("faqs", [])
        self.by_slug = {c["slug"]: c for c in self.concepts}
        self.by_term = {c["term"]: c for c in self.concepts}
        self._alias: dict[str, dict] = {}
        # 先登记所有正名，再用别名补位（别名不得覆盖正名）
        for c in self.concepts:
            self._alias[c["term"]] = c
            self._alias[c["slug"]] = c
            if c.get("en"):
                self._alias[c["en"].lower()] = c
        for c in self.concepts:
            for a in c.get("aliases") or []:
                self._alias.setdefault(a, c)
        self._faq_grams = [(f, _bigrams(f["question"])) for f in self.faqs]
        self._concept_grams = {
            c["slug"]: (_bigrams(_norm(c["term"])), _bigrams(_norm(c.get("definition", ""))))
            for c in self.concepts
        }

    # ---------- lookup ----------
    def homonyms(self, term: str) -> list[dict]:
        """返回与通用语境同名的登记项（用于提示常见误解）。"""
        items = self.terminology.get("homonyms") or []
        return [h for h in items if h.get("term") == term]

    def resolve(self, term: str) -> dict | None:
        if not term:
            return None
        term = term.strip()
        dep = self._deprecated.get(term)
        if dep and dep.get("replacement"):
            term = str(dep["replacement"]).strip()
        if term in self._alias:
            return self._alias[term]
        if term.lower() in self._alias:
            return self._alias[term.lower()]
        for key, concept in self._alias.items():
            if len(key) >= 2 and key in term:
                return concept
        return None

    def search(self, query: str, limit: int = 10, category: str | None = None) -> list[dict]:
        q = clean(query)
        qn = _norm(q)
        if not qn:
            return []
        qg = _bigrams(qn)
        scored: list[tuple[float, dict]] = []
        for c in self.concepts:
            if category and c.get("category") != category:
                continue
            term = _norm(c["term"])
            en = _norm(c.get("en") or "")
            aliases = [_norm(a) for a in (c.get("aliases") or []) if a]
            score = 0.0
            if qn == term:
                score += 100
            elif en and qn == en:
                score += 95
            elif qn in aliases:
                score += 90
            elif qn in term:
                score += 60
            elif any(qn in a for a in aliases):
                score += 55
            body = _norm(c.get("definition", ""))
            if qn in body:
                score += 30
            # 错字容忍：与术语或别名相近时给部分分
            if len(qn) >= 2:
                ratio = max(
                    [difflib.SequenceMatcher(None, qn, term).ratio()]
                    + [difflib.SequenceMatcher(None, qn, a).ratio() for a in aliases]
                )
                if ratio >= 0.66:
                    score += 45 * ratio
            term_grams, def_grams = self._concept_grams[c["slug"]]
            overlap = _jaccard(qg, term_grams)
            if overlap:
                score += 40 * overlap
            score += 8 * _jaccard(qg, def_grams)
            if score > 0:
                scored.append((score, c))
        scored.sort(key=lambda item: -item[0])
        return [
            {
                "term": c["term"],
                "slug": c["slug"],
                "category": c["category"],
                "kind": c.get("kind", "core"),
                "summary": c.get("short_definition", ""),
                "score": round(score, 1),
            }
            for score, c in scored[:limit]
        ]

    # ---------- answering ----------
    def answer(self, question: str) -> dict:
        """对外入口：先执行「学说与个人分离」政策，再走检索路由。"""
        q = clean(question)
        policy = (self.meta.get("stats") or {}).get("policy") or {}
        excluded = policy.get("excluded_entities") or []
        if q and any(e in q for e in excluded):
            stripped = q
            for e in excluded:
                stripped = stripped.replace(f"{e}的", "").replace(e, "")
            stripped = stripped.strip("，,。？?；; ")
            if len(stripped) >= 4:
                result = self._answer_core(stripped)
                result["policy_note"] = policy.get("answer", "")
                result["question"] = q
                return result
            return {
                "ok": True,
                "type": "policy",
                "question": q,
                "answer": policy.get("answer", ""),
                "context": "",
                "citations": [],
                "related": [],
                "next": [],
                "confidence": "high",
            }
        result = self._answer_core(q)
        hits = [h for h in (self.terminology.get("homonyms") or []) if h.get("term") and h["term"] in q]
        if hits:
            result["homonyms"] = hits
        return result

    _ENUM_RE = re.compile(
        r"([\u4e00-\u9fa5A-Za-z]{2,10}(?:、[\u4e00-\u9fa5A-Za-z]{2,10})+)"
        r"(?:分别|各自)?(?:是什么|指什么|的定义|的含义|各是什么)"
    )

    def _enumeration_answer(self, question: str) -> dict | None:
        m = self._ENUM_RE.search(question)
        if not m:
            return None
        names = [n.strip() for n in m.group(1).split("、") if n.strip()]
        concepts = []
        for name in names:
            c = self.resolve(name)
            if c and c["slug"] not in {x["slug"] for x in concepts}:
                concepts.append(c)
        if len(concepts) < 2:
            return None
        lines, citations = [], []
        for c in concepts:
            lines.append(f"【{c['term']}】{c['definition']}")
            if c.get("sources"):
                s0 = c["sources"][0]
                citations.append({"doc": s0["doc_title"], "section": s0.get("section", ""),
                                  "quote": s0.get("quote", ""), "edition": s0.get("edition", "")})
        answer = "\n\n".join(lines)
        related = [{"term": c["term"], "slug": c["slug"],
                    "summary": c.get("short_definition", "")} for c in concepts]
        return {
            "ok": True, "type": "multi", "question": question, "answer": answer,
            "context": self._context_block(answer, citations,
                                           [{"term": c["term"], "summary": c.get("short_definition", "")}
                                            for c in concepts]),
            "citations": citations, "related": related,
            "next": [{"rel": "related", "term": c["term"],
                      "href": f"/api/v1/concept/{c['slug']}"} for c in concepts],
            "confidence": "high",
        }

    def _answer_core(self, question: str) -> dict:
        """复合问句：先试枚举（A、B、C 分别是什么），再按标点拆段路由。"""
        q = clean(question)
        if not q:
            return self._none(q)
        enum = self._enumeration_answer(q)
        if enum is not None:
            return enum
        segments = [seg.strip(" ，,。") for seg in re.split(r"[？?。；;]", q) if seg.strip(" ，,。")]
        if len(segments) > 1:
            fallback = None
            for seg in segments:
                result = self._route_single(seg)
                if result.get("type") in ("relation", "concept", "faq"):
                    result["question"] = q
                    return result
                if fallback is None:
                    fallback = result
            if fallback is not None:
                fallback["question"] = q
                return fallback
        return self._route_single(q)

    def _route_single(self, question: str) -> dict:
        q = clean(question)
        if not q:
            return self._none(q)

        qg = _bigrams(q)
        best_faq, best_score = None, 0.0
        for faq, grams in self._faq_grams:
            if not self._faq_relevant(faq, q):
                continue
            score = _jaccard(qg, grams)
            if score > best_score:
                best_faq, best_score = faq, score

        # 0) 关系型问题：A 与 B 是什么关系 / 有什么区别
        link = self._relation_question(q)
        if link is not None:
            return link

        # 1) 与标准问答高度重合时优先返回问答，避免被术语别名劫持
        if best_faq is not None and best_score >= 0.6:
            return self._from_faq(best_faq, q, best_score)

        # 2) 术语直查：精确命中，或「什么是 X / X 是什么」问法
        concept = self._alias.get(q) or self._alias.get(q.lower()) or self._alias.get(self._strip_question(q))
        if concept is not None:
            return self._from_concept(concept, q)

        # 3) 退一步的问答相似度
        if best_faq is not None and best_score >= 0.34:
            return self._from_faq(best_faq, q, best_score)

        hits = self.search(q, limit=3)
        if hits:
            lines = ["没有直接命中标准问答，以下是相关词条："]
            for h in hits:
                lines.append(f"· {h['term']}：{h['summary']}")
            return {
                "ok": True,
                "type": "related",
                "question": q,
                "answer": "\n".join(lines),
                "context": "\n".join(lines),
                "citations": [],
                "related": hits,
                "did_you_mean": [h["term"] for h in hits],
                "next": [
                    {"rel": "search", "term": h["term"], "href": f"/api/v1/concept/{h['slug']}"}
                    for h in hits
                ],
                "confidence": "low",
            }
        return self._none(q)

    @staticmethod
    def _strip_question(text: str) -> str:
        s = text.strip()
        for prefix in ("请问", "请教", "什么是", "何为", "什么叫"):
            if s.startswith(prefix):
                s = s[len(prefix):]
        for suffix in ("是什么意思", "的定义是什么", "的定义", "是什么", "指什么", "？", "?"):
            if s.endswith(suffix):
                s = s[: -len(suffix)]
        return s.strip("，,。；; ")

    _RELATION_RE = re.compile(
        r"(.{1,20}?)(?:和|与|跟|同)(.{1,20}?)(?:是什么关系|有什么关系|关系是什么|"
        r"有何关系|关系如何|的区别是什么|有什么区别|有何区别|区别是什么)"
    )

    def _relation_question(self, question: str) -> dict | None:
        m = self._RELATION_RE.search(question)
        if not m:
            return None
        a = self.resolve(m.group(1).strip("，,。 "))
        b = self.resolve(m.group(2).strip("，,。 "))
        if not a or not b or a["slug"] == b["slug"]:
            return None

        edge = next((r for r in a.get("relations") or [] if r.get("target") == b["term"]), None)
        reverse = next((r for r in b.get("relations") or [] if r.get("target") == a["term"]), None)
        edge = edge or reverse
        about = ""
        if edge:
            about = f"{a['term']}与{b['term']}的关系是「{edge['type']}」。"
            if edge.get("evidence"):
                about += f"原文：{edge['evidence']}"
        else:
            about = f"知识库中没有直接记录{a['term']}与{b['term']}的关系，以下为两者的定义，供比对。"

        citations = []
        for concept in (a, b):
            if concept.get("sources"):
                s = concept["sources"][0]
                citations.append({"doc": s["doc_title"], "section": s.get("section", ""),
                                  "quote": s.get("quote", ""), "edition": s.get("edition", "")})

        answer = (
            f"{about}\n\n"
            f"【{a['term']}】{a['definition']}\n\n"
            f"【{b['term']}】{b['definition']}"
        )
        return {
            "ok": True,
            "type": "relation",
            "question": question,
            "answer": answer,
            "context": self._context_block(answer, citations, [
                {"term": a["term"], "summary": a.get("short_definition", "")},
                {"term": b["term"], "summary": b.get("short_definition", "")},
            ]),
            "relation": {"source": a["term"], "target": b["term"], "type": edge["type"] if edge else ""},
            "citations": citations,
            "related": [
                {"term": a["term"], "slug": a["slug"], "summary": a.get("short_definition", "")},
                {"term": b["term"], "slug": b["slug"], "summary": b.get("short_definition", "")},
            ],
            "next": [
                {"rel": "related", "term": a["term"], "href": f"/api/v1/concept/{a['slug']}"},
                {"rel": "related", "term": b["term"], "href": f"/api/v1/concept/{b['slug']}"},
            ],
            "confidence": "high" if edge else "medium",
        }

    def _from_faq(self, faq: dict, question: str, score: float) -> dict:
        return {
            "ok": True,
            "type": "faq",
            "question": question,
            "answer": faq["answer"],
            "context": self._context_block(faq["answer"], self._faq_citations(faq),
                                           self._related_entries(faq.get("related") or [])),
            "citations": self._faq_citations(faq),
            "related": self._related_entries(faq.get("related") or []),
            "next": [
                {"rel": "related", "term": r["term"], "href": f"/api/v1/concept/{r['slug']}"}
                for r in self._related_entries(faq.get("related") or [])[:6]
            ],
            "confidence": "high" if score >= 0.6 else "medium",
            "matched_question": faq["question"],
            "score": round(score, 3),
        }

    def _none(self, question: str) -> dict:
        hits = self.search(question, limit=3)
        return {
            "ok": True,
            "type": "none",
            "question": question,
            "answer": "知识库中未找到与该问题匹配的术语或问答。",
            "context": "",
            "citations": [],
            "related": [],
            "did_you_mean": [h["term"] for h in hits],
            "next": [
                {"rel": "search", "term": h["term"], "href": f"/api/v1/concept/{h['slug']}"}
                for h in hits
            ],
            "confidence": "low",
        }

    def _next_links(self, concept: dict) -> list[dict]:
        out = []
        for r in (concept.get("relations") or [])[:6]:
            if not r.get("target_id") or r.get("target") == concept.get("term"):
                continue
            out.append({"rel": r["type"], "term": r["target"],
                        "href": f"/api/v1/concept/{r['target_id']}"})
        return out

    @staticmethod
    def _context_block(answer: str, citations: list[dict], related: list[dict]) -> str:
        """可直接注入上下文的紧凑块：答案 + 出处原句 + 相关概念一句话。"""
        parts = [answer]
        for c in citations[:2]:
            quote = (c.get("quote") or "")[:160]
            if quote:
                parts.append(f"出处（{c.get('doc', '')}）：{quote}")
        for r in related[:4]:
            if r.get("summary"):
                parts.append(f"相关：{r['term']} —— {r['summary']}")
        return "\n".join(parts)[:900]

    def _from_concept(self, concept: dict, question: str) -> dict:
        citations = [
            {"doc": s["doc_title"], "section": s.get("section", ""),
             "quote": s.get("quote", ""), "edition": s.get("edition", "")}
            for s in (concept.get("sources") or [])[:2]
        ]
        evidence = sorted(concept.get("evidence") or [], key=lambda e: -e.get("score", 0))
        if evidence:
            top = evidence[0]
            citations.append({
                "doc": top["doc_title"],
                "section": top.get("section", ""),
                "quote": top["quote"],
                "edition": top.get("edition", ""),
            })
        return {
            "ok": True,
            "type": "concept",
            "question": question,
            "term": concept["term"],
            "answer": concept["definition"],
            "definition_type": concept.get("definition_type", "quote"),
            "editor_note": concept.get("editor_note", ""),
            "short_answer": concept.get("short_definition", ""),
            "context": self._context_block(
                concept["definition"], citations,
                [{"term": r["target"], "summary": (self.by_term.get(r["target"]) or {}).get("short_definition", "")}
                 for r in (concept.get("relations") or [])[:4]],
            ),
            "citations": citations,
            "related": [
                {"term": r["target"], "slug": r.get("target_id", ""), "relation": r["type"]}
                for r in (concept.get("relations") or [])[:8]
            ],
            "next": self._next_links(concept),
            "confidence": "high" if concept.get("status") == "ok" else "medium",
            "homonyms": self.homonyms(concept["term"]),
        }

    @staticmethod
    def _faq_relevant(faq: dict, question: str) -> bool:
        terms = [t for t in (faq.get("source_terms") or []) if t]
        if not terms:
            return True
        return any(t in question for t in terms)

    def _faq_citations(self, faq: dict) -> list[dict]:
        out = []
        for term in faq.get("source_terms") or []:
            concept = self.by_term.get(term)
            if concept and concept.get("sources"):
                s = concept["sources"][0]
                out.append({"doc": s["doc_title"], "section": s.get("section", ""),
                            "quote": s.get("quote", ""), "edition": s.get("edition", "")})
                break
        return out

    def _related_entries(self, ids: list[str]) -> list[dict]:
        out = []
        for i in ids:
            c = self.by_slug.get(i)
            if c:
                out.append({"term": c["term"], "slug": c["slug"], "summary": c.get("short_definition", "")})
        return out

    # ---------- graph ----------
    def related(self, term: str, depth: int = 1, include_mentions: bool = True) -> dict:
        concept = self.resolve(term)
        if concept is None:
            return {"ok": False, "error": f"未找到术语：{term}"}
        nodes = {concept["slug"]: {
            "term": concept["term"], "slug": concept["slug"],
            "category": concept["category"], "kind": concept.get("kind", "core"),
            "summary": concept.get("short_definition", ""),
        }}
        edges = []
        frontier = [concept]
        for _ in range(max(1, min(depth, 2))):
            nxt = []
            for node in frontier:
                for r in node.get("relations") or []:
                    if not include_mentions and r.get("tier") == "mention":
                        continue
                    target = self.by_slug.get(r.get("target_id", ""))
                    if not target:
                        continue
                    edges.append({"source": node["term"], "target": target["term"],
                                  "type": r["type"], "tier": r.get("tier", "core")})
                    if target["slug"] not in nodes:
                        nodes[target["slug"]] = {
                            "term": target["term"], "slug": target["slug"],
                            "category": target["category"], "kind": target.get("kind", "core"),
                            "summary": target.get("short_definition", ""),
                        }
                        nxt.append(target)
            frontier = nxt
        return {"ok": True, "center": concept["term"], "nodes": list(nodes.values()), "edges": edges}

    def catalog(self, category: str | None = None) -> dict:
        items = [
            {
                "term": c["term"], "slug": c["slug"], "category": c["category"],
                "kind": c.get("kind", "core"), "en": c.get("en", ""),
                "summary": c.get("short_definition", ""),
            }
            for c in self.concepts
            if not category or c["category"] == category
        ]
        return {"count": len(items), "categories": self.meta.get("stats", {}).get("categories", {}), "items": items}


_cache: dict[str, tuple[float, Knowledge]] = {}


def load(root: str | Path) -> Knowledge:
    path = Path(root) / "data" / "kb.json"
    if not path.exists():
        from . import pipeline
        pipeline.rebuild(root)
    mtime = path.stat().st_mtime
    cached = _cache.get(str(path))
    if cached and cached[0] == mtime:
        return cached[1]
    payload = json.loads(path.read_text(encoding="utf-8"))
    kb = Knowledge(payload)
    _cache[str(path)] = (mtime, kb)
    return kb


def answer_markdown(result: dict) -> str:
    """把问答结果渲染成便于 Agent 直接嵌入回答的 Markdown。"""
    lines = [f"**{result.get('question', '')}**", "", result.get("answer", "")]
    cites = result.get("citations") or []
    if cites:
        lines += ["", "出处："]
        for c in cites[:3]:
            lines.append(f"- {c.get('doc', '')}（{c.get('section', '')}）：{c.get('quote', '')[:120]}")
    related = result.get("related") or []
    if related:
        lines += ["", "相关概念：" + "、".join(r.get("term", "") for r in related[:5] if r.get("term"))]
    if result.get("did_you_mean"):
        lines += ["", "你可能想问：" + "、".join(result["did_you_mean"])]
    return "\n".join(lines)
