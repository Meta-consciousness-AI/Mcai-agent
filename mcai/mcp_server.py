"""MCP（Model Context Protocol）服务器：stdio + JSON-RPC 2.0。

让 Claude Desktop / Cursor / 其他 Agent 把元意识知识库当作工具与资源直接调用。
启动：python run.py mcp
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import knowledge

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "mcai-knowledge", "version": "0.2.8"}

TOOLS = [
    {
        "name": "mcai_answer",
        "title": "Answer doctrine questions",
        "description": "Answer full-sentence questions about the Meta-Consciousness Theory, returning authoritative definitions, source quotations, and related concepts. Use when the user asks in natural language and does not need one specific entry, e.g. \"What is meta-consciousness?\", \"How are meta-recognition and meta-knowledge related?\", \"How does the progenerative agent explain AI emergence?\". Routing: for a known term and its full entry (aliases, sources, citations, relations) use mcai_concept; if unsure of the exact term use mcai_search; for a catalog use mcai_list; for relations only use mcai_related. Boundary: answers come only from this knowledge base; unlisted concepts return type=none. Do not extrapolate, complete, or introduce meanings outside the corpus.",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "A complete natural-language question, ideally 5–120 characters, one question per call; Chinese or English is fine. Include the exact term when possible, e.g. \"什么是元意识\" or \"元灵和元子有什么区别\".",
                    "examples": [
                        "什么是元意识",
                        "元灵和元子有什么区别"
                    ]
                },
                "format": {
                    "type": "string",
                    "enum": ["full", "citations"],
                    "default": "full",
                    "description": "full returns the answer with citations; citations returns only the source citations for the answer, for RAG or audit use."
                }
            },
            "required": [
                "question"
            ],
            "additionalProperties": False
        }
    },
    {
        "name": "mcai_concept",
        "title": "Get a concept entry",
        "description": "Get the complete entry for a single concept by term, alias, or slug: definition, aliases, sources, source quotations, and relations. Use when the exact term is known and full detail is needed. Routing: if the spelling is uncertain use mcai_search first; for full-sentence questions use mcai_answer; for relations only use mcai_related. Boundary: returns only entries in this knowledge base, with an explicit error when not found.",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "term": {
                    "type": "string",
                    "description": "Exact term, alias, or slug, e.g. 元意识 / MCAI / meta-consciousness; use mcai_search first if unsure.",
                    "examples": [
                        "元意识",
                        "meta-consciousness"
                    ]
                }
            },
            "required": [
                "term"
            ],
            "additionalProperties": False
        }
    },
    {
        "name": "mcai_search",
        "title": "Search terms",
        "description": "Search concepts in the term base. Supports Chinese keywords, English terms, and aliases; results can be filtered by category. Use when the user remembers only an approximate name or needs to confirm a term. Routing: with a term in hand use mcai_concept for the full entry; for full-sentence questions use mcai_answer; for the whole catalog use mcai_list. Boundary: term matching only, no semantic reasoning.",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keywords (2–20 characters recommended; do not pass a full sentence). Supports Chinese, English, or aliases, e.g. 元意识 / progenerative agent / 序生.",
                    "examples": [
                        "元意识",
                        "序生"
                    ]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results, default 8, range 1–30.",
                    "default": 8,
                    "minimum": 1,
                    "maximum": 30
                },
                "category": {
                    "type": "string",
                    "description": "Filter by category; must be one of: 元意识体系 / 本体论模型 / 序生体系 / 元子社会; leave empty for all categories."
                }
            },
            "required": [
                "query"
            ],
            "additionalProperties": False
        }
    },
    {
        "name": "mcai_related",
        "title": "Get relation subgraph",
        "description": "Get the relation subgraph around a concept (including derived relations) to explain causal, structural, or hierarchical links. Use for questions such as \"How are A and B related?\" or \"What are this concept's parents and children?\". Routing: full entry -> mcai_concept; full-sentence explanation -> mcai_answer; finding a term -> mcai_search. Boundary: returns only relations registered in the base and states explicitly when none exist.",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "term": {
                    "type": "string",
                    "description": "Central term; must be a term in the base, e.g. 元意识 / 序生智能体; use mcai_search first if unsure.",
                    "examples": [
                        "元意识",
                        "序生智能体"
                    ]
                },
                "depth": {
                    "type": "integer",
                    "description": "Relation depth: 1 for direct relations, 2 for two hops; default 1.",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 2
                },
                "include_mentions": {
                    "type": "boolean",
                    "description": "Include weak co-occurrence ('mention') edges. Default false returns only curated core/derived relations; set true to include mention edges.",
                    "default": False
                }
            },
            "required": [
                "term"
            ],
            "additionalProperties": False
        }
    },
    {
        "name": "mcai_list",
        "title": "List all terms",
        "description": "List all terms in the knowledge base, optionally filtered by category, to show coverage or let the user choose from a catalog. Use when the user asks \"What concepts does this theory have?\" or \"What do you cover?\". Routing: keyword lookup -> mcai_search; full entry -> mcai_concept. Boundary: returns term names and categories only, not full definitions.",
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by category; must be one of: 元意识体系 / 本体论模型 / 序生体系 / 元子社会; leave empty for all categories."
                }
            },
            "additionalProperties": False
        }
    }
]


PROMPTS = [
    {
        "name": "explain_concept",
        "description": "Explain a term using the Meta-Consciousness Theory definition, distinguishing homonyms.",
        "arguments": [{"name": "term", "description": "Term name", "required": True}],
    },
    {
        "name": "analyze_phenomenon",
        "description": "Analyze a phenomenon with the Meta-Consciousness Theory framework: retrieve definitions first, then reason.",
        "arguments": [{"name": "phenomenon", "description": "Phenomenon or question", "required": True}],
    },
    {
        "name": "compare_terms",
        "description": "Compare two terms: retrieve both definitions and their relations before answering.",
        "arguments": [
            {"name": "a", "description": "Term A", "required": True},
            {"name": "b", "description": "Term B", "required": True},
        ],
    },
]

def _text(payload: dict | list | str) -> dict:
    body = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=2)
    return {"content": [{"type": "text", "text": body}], "isError": False}


def _error(message: str) -> dict:
    return {"content": [{"type": "text", "text": message}], "isError": True}


def call_tool(kb: knowledge.Knowledge, name: str, args: dict) -> dict:
    if name == "mcai_answer":
        result = kb.answer(str(args.get("question", "")))
        if str(args.get("format", "full")).lower() in ("citations", "cite"):
            return _text({
                "question": result.get("question", ""),
                "type": result.get("type"),
                "citations": result.get("citations", []),
            })
        return _text(result)
    if name == "mcai_concept":
        concept = kb.resolve(str(args.get("term", "")))
        if not concept:
            return _error(f"未找到术语：{args.get('term', '')}")
        payload = {k: concept.get(k) for k in (
            "id", "term", "en", "aliases", "category", "kind", "parent",
            "definition", "short_definition", "status", "sources", "evidence", "relations",
        )}
        payload["homonyms"] = kb.homonyms(concept["term"])
        return _text(payload)
    if name == "mcai_search":
        limit = int(args.get("limit", 8) or 8)
        return _text({"query": args.get("query", ""),
                      "results": kb.search(str(args.get("query", "")), limit=limit,
                                           category=args.get("category"))})
    if name == "mcai_related":
        depth = int(args.get("depth", 1) or 1)
        include_mentions = bool(args.get("include_mentions", False))
        return _text(kb.related(str(args.get("term", "")), depth=depth,
                                include_mentions=include_mentions))
    if name == "mcai_list":
        return _text(kb.catalog(args.get("category")))
    return _error(f"未知工具：{name}")


def handle(kb: knowledge.Knowledge, request: dict, tele=None) -> dict | None:
    """处理单条 JSON-RPC 请求；通知类返回 None。"""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params") or {}

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            "serverInfo": SERVER_INFO,
        }}
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments") or {}
        try:
            result = call_tool(kb, name, args)
            if tele is not None:
                query = str(args.get("question") or args.get("term") or args.get("query") or "")
                rtype = ""
                if name == "mcai_answer" and not result.get("isError"):
                    try:
                        rtype = json.loads(result["content"][0]["text"]).get("type", "")
                    except (json.JSONDecodeError, KeyError, IndexError):
                        rtype = ""
                tele.record("mcp", name, query, rtype, ok=not result.get("isError", False))
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except Exception as exc:  # noqa: BLE001
            return {"jsonrpc": "2.0", "id": req_id,
                    "result": _error(f"工具执行失败：{type(exc).__name__}: {exc}")}
    if method == "prompts/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"prompts": PROMPTS}}
    if method == "prompts/get":
        name = params.get("name", "")
        args = params.get("arguments") or {}
        if name == "explain_concept":
            term = args.get("term", "元意识")
            text = (f"请调用 mcai_concept 获取「{term}」的定义与引证，然后用该学说的术语解释它。"
                    f"必须先说明它不是什么（若有消歧信息），再给出定义。")
        elif name == "analyze_phenomenon":
            phenomenon = args.get("phenomenon", "")
            text = (f"请先用 mcai_search 检索与「{phenomenon}」相关的术语，"
                    f"再用 mcai_answer 获取定义与出处，最后用该学说框架分析这个现象。"
                    f"引用必须带出处，不确定时说明知识库未涉及。")
        elif name == "compare_terms":
            text = (f"请分别调用 mcai_concept 获取「{args.get('a', '')}」与「{args.get('b', '')}」的定义，"
                    f"再调用 mcai_related 查看两者关系，最后按「相同点 / 不同点 / 关系类型」作答。")
        else:
            return {"jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -32602, "message": f"未知 prompt：{name}"}}
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "description": next((p["description"] for p in PROMPTS if p["name"] == name), ""),
            "messages": [{"role": "user", "content": {"type": "text", "text": text}}],
        }}
    if method == "resources/list":
        resources = [{
            "uri": "mcai://guide",
            "name": "Agent 接入指南",
            "description": "何时调用、返回结构、术语边界与引用规范",
            "mimeType": "text/markdown",
        }] + [
            {
                "uri": f"mcai://concepts/{c['slug']}",
                "name": c["term"],
                "description": c.get("short_definition", ""),
                "mimeType": "text/markdown",
            }
            for c in kb.concepts
        ]
        return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": resources}}
    if method == "resources/read":
        uri = params.get("uri", "")
        if uri == "mcai://guide":
            from .guide import build_guide
            return {"jsonrpc": "2.0", "id": req_id, "result": {"contents": [{
                "uri": uri, "mimeType": "text/markdown",
                "text": build_guide(kb, kb.payload.get("meta", {}).get("project", {})),
            }]}}
        slug = uri.rsplit("/", 1)[-1] if uri.startswith("mcai://concepts/") else uri
        concept = kb.by_slug.get(slug)
        if not concept:
            return {"jsonrpc": "2.0", "id": req_id,
                    "error": {"code": -32602, "message": f"未知资源：{uri}"}}
        return {"jsonrpc": "2.0", "id": req_id, "result": {"contents": [{
            "uri": uri,
            "mimeType": "text/markdown",
            "text": _concept_markdown(concept),
        }]}}
    return {"jsonrpc": "2.0", "id": req_id,
            "error": {"code": -32601, "message": f"不支持的方法：{method}"}}


def _concept_markdown(c: dict) -> str:
    lines = [f"# {c['term']}", ""]
    if c.get("en"):
        lines.append(f"*{c['en']}*")
    if c.get("aliases"):
        lines.append(f"别名：{'、'.join(c['aliases'])}")
    lines += ["", c["definition"], "", f"分类：{c['category']}"]
    if c.get("parent"):
        lines.append(f"衍生自：{c['parent']}")
    if c.get("sources"):
        lines += ["", "## 定义来源"]
        lines += [f"- {s['doc_title']}（{s.get('section', '')}）" for s in c["sources"]]
    if c.get("evidence"):
        lines += ["", "## 文献引证"]
        lines += [f"- 「{e['quote']}」——{e['doc_title']}" for e in c["evidence"][:3]]
    if c.get("relations"):
        lines += ["", "## 相关概念"]
        lines += [f"- {r['target']}（{r['type']}）" for r in c["relations"][:10]]
    return "\n".join(lines)


def main(root: str | Path) -> None:
    from .telemetry import for_root
    kb = knowledge.load(root)
    tele = for_root(root)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "id": None,
                              "error": {"code": -32700, "message": "JSON 解析失败"}}, ensure_ascii=False),
                  flush=True)
            continue
        response = handle(kb, request, tele)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)


def main_entry() -> None:
    """控制台入口（mcai-mcp）：按 MCAI_HOME / 当前目录解析工作区。"""
    from .workspace import resolve_home
    main(resolve_home(None))
