# -*- coding: utf-8 -*-
"""质量巡检与接口自测。"""
import json
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai import quality, selftest  # noqa: E402


def kb_stub(**overrides) -> dict:
    concept = {
        "term": "元意识", "slug": "meta-consciousness",
        "definition": "元意识是宇宙的本源，不可描述。", "status": "ok",
        "sources": [{"doc_title": "词表"}], "en": "Meta-consciousness",
        "relations": [], "_": "",
    }
    concept.update(overrides)
    return {
        "meta": {"stats": {"disambiguation": {"enabled": True}, "coverage": {"missing": []}}},
        "concepts": [concept],
        "faqs": [{"question": "什么是元意识？", "answer": "宇宙本源。", "campaign": False}],
    }


class QualityTest(unittest.TestCase):
    def test_clean_kb(self) -> None:
        issues = quality.check_kb(kb_stub())
        errors = [i for i in issues if i["level"] == "error"]
        self.assertEqual(errors, [])

    def test_thin_definition(self) -> None:
        issues = quality.check_kb(kb_stub(definition="短"))
        self.assertTrue(any(i["code"] == "concept.thin" for i in issues))

    def test_dangling_relation(self) -> None:
        issues = quality.check_kb(kb_stub(relations=[{"target": "不存在", "target_id": "nope"}]))
        self.assertTrue(any(i["code"] == "relation.dangling" for i in issues))

    def test_duplicate_faq(self) -> None:
        kb = kb_stub()
        kb["faqs"].append(dict(kb["faqs"][0]))
        issues = quality.check_kb(kb)
        self.assertTrue(any(i["code"] == "faq.duplicate" for i in issues))

    def test_campaign_leak(self) -> None:
        kb = kb_stub()
        kb["meta"]["stats"]["disambiguation"]["enabled"] = False
        kb["faqs"].append({"question": "X 是 Y 吗？", "answer": "不是。", "campaign": True})
        issues = quality.check_kb(kb)
        self.assertTrue(any(i["code"] == "campaign.leak" for i in issues))

    def test_inspect_real_workspace(self) -> None:
        result = quality.inspect(ROOT)
        self.assertIn("counts", result)
        self.assertEqual(result["counts"]["error"], 0)
        self.assertTrue((ROOT / "data" / "quality.json").exists())


class SelftestTest(unittest.TestCase):
    def test_selftest_passes(self) -> None:
        result = selftest.run(ROOT)
        self.assertTrue(result["ok"], result["failed"])
        self.assertGreaterEqual(result["passed"], 10)
        self.assertTrue((ROOT / "data" / "selftest.json").exists())

    def test_selftest_structure(self) -> None:
        result = selftest.run(ROOT)
        names = {c["name"] for c in result["checks"]}
        self.assertIn("mcp.initialize", names)
        self.assertIn("tool.mcai_answer", names)


if __name__ == "__main__":
    unittest.main()
