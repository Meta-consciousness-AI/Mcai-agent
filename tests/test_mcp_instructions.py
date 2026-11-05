import unittest
from pathlib import Path

from mcai import knowledge, mcp_server

ROOT = Path(__file__).resolve().parent.parent


class McpInstructionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kb = knowledge.load(ROOT)

    def _call(self, method, params=None):
        return mcp_server.handle(
            self.kb,
            {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}},
        )

    def test_initialize_carries_routing_instructions(self):
        result = self._call("initialize")["result"]
        self.assertIn("instructions", result)
        text = result["instructions"]
        for tool in ("mcai_answer", "mcai_concept", "mcai_search", "mcai_related", "mcai_list"):
            self.assertIn(tool, text)
        self.assertIn("type='none'", text)

    def test_every_tool_description_has_routing(self):
        tools = self._call("tools/list")["result"]["tools"]
        self.assertEqual(
            [t["name"] for t in tools],
            ["mcai_answer", "mcai_concept", "mcai_search", "mcai_related", "mcai_list"],
        )
        for tool in tools:
            self.assertIn("Routing", tool["description"], tool["name"])
            self.assertTrue(tool["annotations"]["readOnlyHint"], tool["name"])

    def test_answer_description_mentions_fallback(self):
        tools = self._call("tools/list")["result"]["tools"]
        answer = next(t for t in tools if t["name"] == "mcai_answer")
        self.assertIn("mcai_search", answer["description"])
        self.assertIn("type='none'", answer["description"])


if __name__ == "__main__":
    unittest.main()
