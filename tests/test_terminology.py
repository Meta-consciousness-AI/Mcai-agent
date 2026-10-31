import json
import unittest
from pathlib import Path

from mcai.knowledge import load

ROOT = Path(__file__).resolve().parent.parent


class TerminologyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kb = load(ROOT)

    def test_homonyms_registered(self):
        rows = self.kb.homonyms("元意识")
        self.assertTrue(rows)
        self.assertTrue(rows[0].get("other_sense"))

    def test_concept_answer_exposes_homonyms(self):
        data = self.kb.answer("什么是元意识")
        self.assertIn("homonyms", data)
        self.assertTrue(data["homonyms"])

    def test_deprecated_mapping(self):
        # 登记表存在且结构正确；当前没有废弃术语
        self.assertIsInstance(self.kb.terminology.get("deprecated"), list)


class RelationTierTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kb = load(ROOT)

    def test_relations_have_tier(self):
        concept = self.kb.resolve("元识")
        self.assertTrue(concept)
        self.assertTrue(all("tier" in r for r in concept["relations"]))

    def test_core_only_excludes_mentions(self):
        result = self.kb.related("元识", depth=1, include_mentions=False)
        self.assertTrue(result["ok"])
        self.assertTrue(all(e.get("tier") != "mention" for e in result["edges"]))

    def test_with_mentions_includes_them(self):
        result = self.kb.related("元识", depth=1, include_mentions=True)
        tiers = {e.get("tier") for e in result["edges"]}
        self.assertIn("mention", tiers)


class ConceptVersionLogTest(unittest.TestCase):
    def test_version_log_exists_after_build(self):
        path = ROOT / "data" / "concept_versions.jsonl"
        self.assertTrue(path.exists())
        first = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
        self.assertIn("term", first)
        self.assertIn("hash", first)


if __name__ == "__main__":
    unittest.main()
