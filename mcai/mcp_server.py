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
SERVER_INFO = {"name": "mcai-knowledge", "version": "0.2.0"}

TOOLS = [
    {
        "name": "mcai_answer",
        "description": (
            "回答关于元意识学说的问题。返回权威定义、原文引证与相关概念。"
            "适合回答“什么是元意识”“序生智能体与AI涌现的关系”等问题。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "用户问题，中英文均可"},
            },
            "required": ["question"],
        },
    },
    {
        "name": "mcai_concept",
        "description": "按术语名、别名或 slug 获取单个概念的完整词条（定义、别名、出处、引证、关系）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "term": {"type": "string", "description": "术语、别名或 slug，如 元意识 / MCAI / meta-consciousness"},
            },
            "required": ["term"],
        },
    },
    {
        "name": "mcai_search",
        "description": "在术语库中检索概念，支持中文关键词、英文词与别名，可按体系过滤。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 8, "minimum": 1, "maximum": 30},
                "category": {
                    "type": "string",
                    "description": "可选：元意识体系 / 本体论模型 / 序生体系 / 元子社会",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "mcai_related",
        "description": "获取概念的关系子图（含衍生关系），用于解释概念之间的因果与结构。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "term": {"type": "string"},
                "depth": {"type": "integer", "default": 1, "minimum": 1, "maximum": 2},
            },
            "required": ["term"],
        },
    },
    {
        "name": "mcai_list",
        "description": "列出全部术语（可按体系过滤），用于了解知识库覆盖范围。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
            },
        },
    },
]


PROMPTS = [
    {
        "name": "explain_concept",
        "description": "用元意识学说的定义解释一个术语，要求区分同名概念。",
        "arguments": [{"name": "term", "description": "术语名", "required": True}],
    },
    {
        "name": "analyze_phenomenon",
        "description": "用元意识学说的框架分析一个现象，先取定义再推理。",
        "arguments": [{"name": "phenomenon", "description": "现象或问题", "required": True}],
    },
    {
        "name": "compare_terms",
        "description": "比较两个术语，先取两者定义与关系再作答。",
        "arguments": [
            {"name": "a", "description": "术语 A", "required": True},
            {"name": "b", "description": "术语 B", "required": True},
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
        return _text(kb.answer(str(args.get("question", ""))))
    if name == "mcai_concept":
        concept = kb.resolve(str(args.get("term", "")))
        if not concept:
            return _error(f"未找到术语：{args.get('term', '')}")
        return _text({k: concept.get(k) for k in (
            "id", "term", "en", "aliases", "category", "kind", "parent",
            "definition", "short_definition", "status", "sources", "evidence", "relations",
        )})
    if name == "mcai_search":
        limit = int(args.get("limit", 8) or 8)
        return _text({"query": args.get("query", ""),
                      "results": kb.search(str(args.get("query", "")), limit=limit,
                                           category=args.get("category"))})
    if name == "mcai_related":
        depth = int(args.get("depth", 1) or 1)
        return _text(kb.related(str(args.get("term", "")), depth=depth))
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
