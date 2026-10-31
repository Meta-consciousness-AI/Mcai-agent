import json
import unittest
from pathlib import Path

from mcai.knowledge import load

ROOT = Path(__file__).resolve().parent.parent


class EditionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kb = load(ROOT)

    def test_all_sources_have_edition(self):
        for c in self.kb.concepts:
            for s in c.get("sources") or []:
                self.assertTrue(s.get("edition"), f"{c['term']} 缺少 edition")

    def test_answer_citation_carries_edition(self):
        data = self.kb.answer("什么是元识")
        self.assertTrue(data["citations"])
        for cite in data["citations"]:
            self.assertIn("edition", cite)

    def test_provenance_dataset_has_edition(self):
        path = ROOT / "dist" / "dataset" / "provenance.jsonl"
        if not path.exists():
            self.skipTest("dataset 未生成")
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertTrue(rows)
        self.assertTrue(all(r.get("edition") for r in rows))


if __name__ == "__main__":
    unittest.main()
