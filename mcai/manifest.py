"""对外可发现性清单：让别的 AI / Agent 能自动找到并接入。

生成三个机器可读文件：
- /.well-known/mcp.json   MCP 服务器清单（传输方式、工具、示例）
- /.well-known/agent.json Agent Card（能力、技能、入口）
- /openapi.json           HTTP API 的 OpenAPI 3.1 描述
"""
from __future__ import annotations

from .extract import KnowledgeBase


def _base(project: dict) -> str:
    return project["site_url"].rstrip("/")


def mcp_manifest(kb: KnowledgeBase, project: dict) -> dict:
    from .mcp_server import PROTOCOL_VERSION, SERVER_INFO, TOOLS

    base = _base(project)
    return {
        "name": SERVER_INFO["name"],
        "displayName": f"{project['brand']}学说知识库",
        "description": (
            f"可被其他 Agent 调用的{project['brand']}学说知识库："
            f"{kb.stats['concepts']} 个术语定义、{kb.stats['faqs']} 组问答、"
            f"{kb.stats['relations']} 条概念关系，全部带原文出处。"
        ),
        "version": SERVER_INFO["version"],
        "protocolVersion": PROTOCOL_VERSION,
        "transport": {"type": "stdio", "command": "python", "args": ["run.py", "mcp"]},
        "capabilities": {"tools": True, "resources": True, "prompts": False},
        "tools": [
            {
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["inputSchema"],
            }
            for t in TOOLS
        ],
        "http": {
            "base": f"{base}/api/v1",
            "endpoints": ["health", "catalog", "search", "concept/<slug>", "answer", "answer/batch",
                           "related"],
            "localOnly": ["stats", "gaps"],
            "auth": "none (local) / Bearer token (public)",
        },
        "examples": [
            {"tool": "mcai_answer", "arguments": {"question": "什么是元意识？"}},
            {"tool": "mcai_search", "arguments": {"query": "序生", "limit": 5}},
            {"tool": "mcai_related", "arguments": {"term": "元意识", "depth": 1}},
        ],
        "license": project.get("license", ""),
        "publisher": project.get("org", ""),
    }


def agent_card(kb: KnowledgeBase, project: dict) -> dict:
    base = _base(project)
    return {
        "name": f"{project['brand']}知识 Agent",
        "description": (
            f"回答关于{project['brand']}学说的问题，提供术语定义、概念关系与原文引证；"
            "不臆造理论，资料未涉及时会明确说明。"
        ),
        "url": base,
        "version": project.get("version", "0.1.0"),
        "provider": {"organization": project.get("org", ""), "url": base},
        "capabilities": {"streaming": False, "pushNotifications": False, "stateTransitionHistory": False},
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["application/json", "text/markdown"],
        "skills": [
            {
                "id": "mcai_answer",
                "name": "学说问答",
                "description": "基于术语表与文献引证回答问题，返回定义、出处与相关概念。",
                "examples": ["什么是元意识？", "序生智能体与AI涌现是什么关系？"],
            },
            {
                "id": "mcai_search",
                "name": "术语检索",
                "description": "按中文、英文或别名检索术语。",
                "examples": ["搜索 元知", "search meta-consciousness"],
            },
            {
                "id": "mcai_related",
                "name": "概念关系",
                "description": "返回概念的关系子图，用于解释结构。",
                "examples": ["元意识和元态能量是什么关系？"],
            },
        ],
        "endpoints": {
            "mcp": f"{base}/.well-known/mcp.json",
            "http": f"{base}/api/v1",
            "openapi": f"{base}/openapi.json",
            "llms": f"{base}/llms.txt",
        },
    }


def openapi(kb: KnowledgeBase, project: dict) -> dict:
    base = _base(project)

    def ok(schema: dict) -> dict:
        return {"200": {"description": "OK", "content": {"application/json": {"schema": schema}}} }

    return {
        "openapi": "3.1.0",
        "info": {
            "title": f"{project['brand']}知识库 API",
            "version": project.get("version", "0.1.0"),
            "description": f"术语、问答与概念关系查询。共 {kb.stats['concepts']} 个术语。",
        },
        "servers": [{"url": f"{base}/api/v1"}],
        "paths": {
            "/health": {"get": {"summary": "健康检查", "responses": ok({"type": "object"})}},
            "/catalog": {
                "get": {
                    "summary": "术语目录",
                    "parameters": [{"name": "category", "in": "query", "schema": {"type": "string"}}],
                    "responses": ok({"type": "object"}),
                }
            },
            "/search": {
                "get": {
                    "summary": "检索术语",
                    "parameters": [
                        {"name": "q", "in": "query", "required": True, "schema": {"type": "string"}},
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 8}},
                    ],
                    "responses": ok({"type": "object"}),
                }
            },
            "/concept/{slug}": {
                "get": {
                    "summary": "获取词条",
                    "parameters": [{"name": "slug", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": ok({"type": "object"}),
                }
            },
            "/answer": {
                "get": {
                    "summary": "问答（GET）",
                    "parameters": [{"name": "q", "in": "query", "required": True, "schema": {"type": "string"}}],
                    "responses": ok({"type": "object"}),
                },
                "post": {
                    "summary": "问答（POST）",
                    "requestBody": {
                        "content": {"application/json": {"schema": {
                            "type": "object", "properties": {"question": {"type": "string"}},
                            "required": ["question"],
                        }}}
                    },
                    "responses": ok({"type": "object"}),
                },
            },
            "/related": {
                "get": {
                    "summary": "关系子图",
                    "parameters": [
                        {"name": "term", "in": "query", "required": True, "schema": {"type": "string"}},
                        {"name": "depth", "in": "query", "schema": {"type": "integer", "enum": [1, 2]}},
                    ],
                    "responses": ok({"type": "object"}),
                }
            },
            "/stats": {"get": {"summary": "调用统计", "responses": ok({"type": "object"})}},
            "/gaps": {"get": {"summary": "未命中的问题（用于补词）", "responses": ok({"type": "object"})}},
        },
    }
