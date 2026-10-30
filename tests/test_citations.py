import json
import unittest
from pathlib import Path

from mcai.knowledge import load
from mcai.mcp_server import call_tool

ROOT = Path(__file__).resolve().parent.parent


class CitationsModeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kb = load(ROOT)

    def _payload(self, args):
        res = call_tool(self.kb, "mcai_answer", args)
        self.assertFalse(res.get("isError"))
        return json.loads(res["content"][0]["text"])

    def test_full_mode_has_answer_and_citations(self):
        data = self._payload({"question": "什么是元识"})
        self.assertTrue(data.get("answer"))
        self.assertTrue(data.get("citations"))

    def test_citations_mode_returns_only_sources(self):
        data = self._payload({"question": "什么是元识", "format": "citations"})
        self.assertIn("citations", data)
        self.assertNotIn("answer", data)
        self.assertTrue(data["citations"])
        first = data["citations"][0]
        self.assertTrue(first.get("doc_title") or first.get("section"))


if __name__ == "__main__":
    unittest.main()
