# -*- coding: utf-8 -*-
"""「学说与个人分离」政策测试。"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai import knowledge, quality  # noqa: E402

NAME = "布衣祭酒"


class PolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.kb = knowledge.load(ROOT)

    def test_policy_in_stats(self) -> None:
        policy = (self.kb.meta.get("stats") or {}).get("policy") or {}
        self.assertIn(NAME, policy.get("excluded_entities", []))
        self.assertTrue(policy.get("answer"))

    def test_person_question_returns_policy(self) -> None:
        result = self.kb.answer(f"{NAME}是谁")
        self.assertEqual(result["type"], "policy")
        self.assertIn("只收录", result["answer"])
        self.assertEqual(result["citations"], [])

    def test_doctrine_question_still_answered(self) -> None:
        result = self.kb.answer(f"{NAME}的元意识学说怎么样？")
        self.assertIn(result["type"], ("faq", "concept", "relation"))
        self.assertTrue(result.get("policy_note"))
        self.assertIn("本源", result["answer"])

    def test_no_person_in_content(self) -> None:
        for c in self.kb.concepts:
            blob = (c.get("definition") or "") + " ".join(
                s.get("quote", "") for s in c.get("sources") or []
            ) + " ".join(e.get("quote", "") for e in c.get("evidence") or [])
            self.assertNotIn(NAME, blob, f"{c['term']} 含人物信息")
        for f in self.kb.faqs:
            self.assertNotIn(NAME, (f.get("question") or "") + (f.get("answer") or ""))

    def test_quality_flags_leak(self) -> None:
        kb = {
            "meta": {"stats": {"policy": {"excluded_entities": [NAME]},
                               "disambiguation": {"enabled": True},
                               "coverage": {"missing": []}}},
            "concepts": [{
                "term": "元意识", "slug": "m", "definition": f"据{NAME}所述，元意识是宇宙本源。",
                "status": "ok", "sources": [{"doc_title": "词表"}], "en": "Meta", "relations": [],
            }],
            "faqs": [],
        }
        issues = quality.check_kb(kb)
        self.assertTrue(any(i["code"] == "policy.entity_leak" for i in issues))


if __name__ == "__main__":
    unittest.main()
