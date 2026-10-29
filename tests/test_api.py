# -*- coding: utf-8 -*-
"""API / MCP 检索层测试。"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai import knowledge, mcp_server  # noqa: E402


class KnowledgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.kb = knowledge.load(ROOT)

    def test_resolve_alias_and_slug(self) -> None:
        self.assertEqual(self.kb.resolve("MCAI")["term"], "元意识")
        self.assertEqual(self.kb.resolve("meta-consciousness")["term"], "元意识")
        self.assertEqual(self.kb.resolve("元意识")["term"], "元意识")
        self.assertIsNone(self.kb.resolve("不存在的术语"))

    def test_answer_definition(self) -> None:
        result = self.kb.answer("什么是元意识？")
        self.assertTrue(result["ok"])
        self.assertIn(result["type"], ("concept", "faq"))
        self.assertIn("本源", result["answer"])
        self.assertTrue(result.get("context"))
        self.assertTrue(result.get("next"))
        self.assertIn("出处", result["context"])

    def test_answer_none_has_suggestions(self) -> None:
        result = self.kb.answer("量子纠缠的退相干时间是多少")
        if result["type"] in ("none", "related"):
            self.assertIn("did_you_mean", result)
            self.assertTrue(result["next"])

    def test_markdown_render(self) -> None:
        md = knowledge.answer_markdown(self.kb.answer("什么是元意识？"))
        self.assertIn("出处", md)

    def test_answer_alias_question(self) -> None:
        result = self.kb.answer("MCAI 是什么？")
        self.assertIn("元意识", json.dumps(result, ensure_ascii=False))

    def test_answer_faq(self) -> None:
        result = self.kb.answer("元意识学说与传统意识哲学有何不同？")
        self.assertEqual(result["type"], "faq")
        self.assertIn("物质与意识", result["answer"])

    def test_search(self) -> None:
        hits = self.kb.search("序生智能体")
        self.assertTrue(hits)
        self.assertEqual(hits[0]["term"], "序生智能体")
        self.assertTrue(all("slug" in h for h in hits))

    def test_related(self) -> None:
        result = self.kb.related("元意识", depth=1)
        self.assertTrue(result["ok"])
        self.assertGreaterEqual(len(result["nodes"]), 2)
        self.assertTrue(result["edges"])

    def test_alias_does_not_hijack_canonical(self) -> None:
        self.assertEqual(self.kb.resolve("元子")["term"], "元子")
        self.assertEqual(self.kb.resolve("元灵")["term"], "元灵")

    def test_compound_question_splits(self) -> None:
        r = self.kb.answer("元识是什么？它的确切定义和作用是什么？")
        self.assertEqual(r["type"], "concept")
        self.assertIn("认知行为", r["answer"])

    def test_relation_not_misrouted_to_faq(self) -> None:
        r = self.kb.answer("元灵和元子有什么区别？")
        self.assertEqual(r["type"], "relation")
        self.assertIn("元灵", r["answer"])
        self.assertIn("元子", r["answer"])

    def test_enumeration_question(self) -> None:
        r = self.kb.answer("元识、元知、元灵、元子分别是什么？")
        self.assertEqual(r["type"], "multi")
        for term in ("元识", "元知", "元灵", "元子"):
            self.assertIn(term, r["answer"])

    def test_derived_concept(self) -> None:
        result = self.kb.answer("绝对实在")
        self.assertEqual(result["type"], "concept")
        self.assertIn("元时空", result["answer"])


class McpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.kb = knowledge.load(ROOT)

    def call(self, method: str, params: dict | None = None, req_id: int = 1) -> dict:
        return mcp_server.handle(self.kb, {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}})

    def test_initialize(self) -> None:
        res = self.call("initialize")
        self.assertEqual(res["result"]["protocolVersion"], mcp_server.PROTOCOL_VERSION)
        self.assertIn("tools", res["result"]["capabilities"])

    def test_tools_list(self) -> None:
        res = self.call("tools/list")
        names = {t["name"] for t in res["result"]["tools"]}
        self.assertEqual(names, {"mcai_answer", "mcai_concept", "mcai_search", "mcai_related", "mcai_list"})

    def test_tool_call_answer(self) -> None:
        res = self.call("tools/call", {"name": "mcai_answer", "arguments": {"question": "什么是序生智能体？"}})
        self.assertFalse(res["result"]["isError"])
        payload = json.loads(res["result"]["content"][0]["text"])
        self.assertIn("序生智能体", payload["answer"])

    def test_tool_call_unknown(self) -> None:
        res = self.call("tools/call", {"name": "nope", "arguments": {}})
        self.assertTrue(res["result"]["isError"])

    def test_resources(self) -> None:
        listing = self.call("resources/list")["result"]["resources"]
        self.assertEqual(len(listing), len(self.kb.concepts) + 1)  # + mcai://guide
        self.assertEqual(listing[0]["uri"], "mcai://guide")
        guide = self.call("resources/read", {"uri": "mcai://guide"})
        self.assertIn("接入指南", guide["result"]["contents"][0]["text"])

    def test_prompts(self) -> None:
        listing = self.call("prompts/list")["result"]["prompts"]
        self.assertEqual(len(listing), 3)
        got = self.call("prompts/get", {"name": "compare_terms", "arguments": {"a": "元识", "b": "元知"}})
        text = got["result"]["messages"][0]["content"]["text"]
        self.assertIn("元识", text)
        self.assertIn("元知", text)

    def test_concept_resource(self) -> None:
        read = self.call("resources/read", {"uri": "mcai://concepts/meta-consciousness"})
        self.assertIn("text/markdown", read["result"]["contents"][0]["mimeType"])
        self.assertIn("元意识", read["result"]["contents"][0]["text"])

    def test_unknown_method(self) -> None:
        res = self.call("does/not/exist")
        self.assertEqual(res["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
