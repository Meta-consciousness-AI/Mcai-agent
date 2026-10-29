"""接口自测：不依赖网络，直接走 MCP 与知识检索内核，确保每次重建后接口没被改坏。"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from . import knowledge, mcp_server


def run(root: str | Path) -> dict:
    root = Path(root)
    kb = knowledge.load(root)
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    # 1. MCP 握手
    init = mcp_server.handle(kb, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    add("mcp.initialize", bool(init and init.get("result", {}).get("protocolVersion")),
        init.get("result", {}).get("protocolVersion", "") if init else "")

    # 2. 工具清单
    tools = mcp_server.handle(kb, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = {t["name"] for t in tools["result"]["tools"]}
    expected = {"mcai_answer", "mcai_concept", "mcai_search", "mcai_related", "mcai_list"}
    add("mcp.tools", names == expected, f"{len(names)} 个工具")

    # 3. 逐个调用
    calls = {
        "mcai_answer": {"question": "什么是元意识？"},
        "mcai_concept": {"term": "元意识"},
        "mcai_search": {"query": "序生", "limit": 3},
        "mcai_related": {"term": "元意识", "depth": 1},
        "mcai_list": {"category": "元意识体系"},
    }
    for name, args in calls.items():
        resp = mcp_server.handle(kb, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                      "params": {"name": name, "arguments": args}})
        ok = bool(resp and resp.get("result") and not resp["result"].get("isError"))
        add(f"tool.{name}", ok)

    # 4. Prompts 与资源
    prompts = mcp_server.handle(kb, {"jsonrpc": "2.0", "id": 4, "method": "prompts/list"})
    add("mcp.prompts", len(prompts["result"]["prompts"]) == 3)
    guide = mcp_server.handle(kb, {"jsonrpc": "2.0", "id": 5, "method": "resources/read",
                                   "params": {"uri": "mcai://guide"}})
    add("resource.guide", "接入指南" in guide["result"]["contents"][0]["text"])

    # 5. 关键问题（仅当知识库足够大时；小工作区跳过，避免误报）
    golden = [
        ("什么是元意识？", {"concept", "faq"}),
        ("元意识和元态能量是什么关系？", {"relation"}),
        ("元意识学说与传统意识哲学有何不同？", {"faq"}),
    ]
    if len(kb.concepts) >= 10:
        for question, expected_types in golden:
            answer = kb.answer(question)
            add(f"golden.{question[:12]}", answer["type"] in expected_types, answer["type"])

    failed = [c for c in checks if not c["ok"]]
    result = {
        "ok": not failed,
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "passed": len(checks) - len(failed),
        "total": len(checks),
        "failed": [c["name"] for c in failed],
        "checks": checks,
    }
    out = root / "data" / "selftest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
