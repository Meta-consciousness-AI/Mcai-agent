# -*- coding: utf-8 -*-
import json
import unittest
from pathlib import Path

from mcai import knowledge, mcp_server

ROOT = Path(__file__).resolve().parent.parent


class CiteProvenanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kb = knowledge.load(str(ROOT))

    def test_tools_registered(self):
        names = [t["name"] for t in mcp_server.TOOLS]
        self.assertIn("mcai_cite", names)
        self.assertIn("mcai_provenance", names)
        self.assertEqual(len(names), 7)

    def test_citations(self):
        payload = self.kb.citations("元意识", limit=2)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["term"], "元意识")
        self.assertGreaterEqual(payload["count"], 1)
        self.assertLessEqual(len(payload["citations"]), 2)
        row = payload["citations"][0]
        for key in ("doc", "quote", "location", "char_start", "char_end"):
            self.assertIn(key, row)
        self.assertTrue(row["quote"].strip())

    def test_provenance(self):
        payload = self.kb.provenance("元意识")
        self.assertIsNotNone(payload)
        for key in ("term", "definition_type", "documents", "sources", "evidence", "relations"):
            self.assertIn(key, payload)
        self.assertGreaterEqual(len(payload["documents"]), 1)
        self.assertTrue(payload["sources"])

    def test_unknown_term(self):
        self.assertIsNone(self.kb.citations("不存在的术语xyz"))
        self.assertIsNone(self.kb.provenance("不存在的术语xyz"))
        result = mcp_server.call_tool(self.kb, "mcai_cite", {"term": "不存在的术语xyz"})
        self.assertTrue(result["isError"])

    def test_mcp_tool_output(self):
        result = mcp_server.call_tool(self.kb, "mcai_provenance", {"term": "元意识"})
        self.assertFalse(result["isError"])
        body = json.loads(result["content"][0]["text"])
        self.assertEqual(body["term"], "元意识")


if __name__ == "__main__":
    unittest.main()
