import unittest
from pathlib import Path

from mcai.knowledge import load

ROOT = Path(__file__).resolve().parent.parent


class SearchRecallTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kb = load(ROOT)

    def top(self, query: str) -> str:
        rows = self.kb.search(query, limit=5)
        self.assertTrue(rows, f"no result for {query}")
        return rows[0]["term"]

    def test_traditional_chinese(self):
        self.assertEqual(self.top("元識"), "元识")

    def test_trailing_punctuation(self):
        self.assertEqual(self.top("元识？"), "元识")

    def test_fullwidth_alias(self):
        self.assertEqual(self.top("ＭＣＡＩ"), "元意识")

    def test_english_name(self):
        self.assertEqual(self.top("meta-recognition"), "元识")

    def test_typo_tolerance(self):
        self.assertEqual(self.top("序生智能休"), "序生智能体")

    def test_definition_keyword(self):
        terms = [row["term"] for row in self.kb.search("认知行为", limit=10)]
        self.assertIn("元识", terms)


if __name__ == "__main__":
    unittest.main()
