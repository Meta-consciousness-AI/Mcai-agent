# -*- coding: utf-8 -*-
"""消歧活动层、遥测与可发现性清单测试。"""
import json
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai import knowledge, manifest, site  # noqa: E402
from mcai.corpus import load_config, load_corpus  # noqa: E402
from mcai.disambig import Disambiguation, load  # noqa: E402
from mcai.extract import build  # noqa: E402
from mcai.telemetry import Telemetry  # noqa: E402


class DisambiguationTest(unittest.TestCase):
    def test_config_loaded(self) -> None:
        dis = load(ROOT / "config" / "disambiguation.json")
        self.assertTrue(dis.active)
        self.assertEqual(len(dis.items), 10)
        self.assertTrue(dis.faq_entries())
        self.assertTrue(dis.note_for("元意识"))

    def test_disabled_campaign_is_silent(self) -> None:
        dis = Disambiguation({"campaign": {"enabled": False}, "items": [
            {"term": "元意识", "confused_with": "元认知", "one_line": "不是元认知。"}
        ]})
        self.assertFalse(dis.active)
        self.assertEqual(dis.faq_entries(), [])
        self.assertEqual(dis.note_for("元意识"), "")
        self.assertIsNone(dis.page_block("元意识"))

    def test_built_kb_keeps_definition_clean(self) -> None:
        kb = knowledge.load(ROOT)
        concept = kb.by_term["元意识"]
        self.assertNotIn("不是", concept["definition"])
        self.assertIn("元认知", concept.get("disambiguation", ""))
        campaign_faqs = [f for f in kb.faqs if f.get("campaign")]
        self.assertEqual(len(campaign_faqs), 10)
        self.assertIn("campaign_faqs", kb.meta["stats"])


class TelemetryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.work = Path(__file__).parent / "_work_tele"
        shutil.rmtree(self.work, ignore_errors=True)
        self.work.mkdir(parents=True)
        self.tele = Telemetry(self.work / "usage.jsonl")

    def tearDown(self) -> None:
        shutil.rmtree(self.work, ignore_errors=True)

    def test_record_and_stats(self) -> None:
        self.tele.record("http", "answer", "什么是元意识", "faq")
        self.tele.record("mcp", "mcai_answer", "什么是序生智能体", "concept")
        self.tele.record("http", "answer", "什么是量子纠缠", "none")
        stats = self.tele.stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["by_channel"]["http"], 2)
        self.assertEqual(stats["by_type"]["faq"], 1)
        self.assertEqual(stats["business"], 3)
        self.assertEqual(stats["probes"], 0)
        self.assertEqual(stats["top_questions"][0]["count"], 1)
        self.assertIn("by_client_kind", stats)
        gaps = self.tele.gaps()
        self.assertEqual(gaps[0]["query"], "什么是量子纠缠")
        self.assertEqual(gaps[0]["count"], 1)

    def test_client_kind_shell(self) -> None:
        self.tele.record("http", "answer", "什么是元意识", "faq",
                         detail={"client": "Mozilla/5.0 (Windows NT) WindowsPowerShell/5.1"})
        self.tele.record("http", "answer", "什么是元意识", "faq",
                         detail={"client": "Python-urllib/3.12"})
        self.tele.record("http", "answer", "什么是元识", "faq",
                         detail={"client": "mcai-skill/1.0 (+doubao-skill)"})
        kinds = self.tele.stats()["by_client_kind"]
        self.assertEqual(kinds.get("shell"), 1)
        self.assertEqual(kinds.get("self"), 1)
        self.assertEqual(kinds.get("skill"), 1)

    def test_batch_types_and_hit_rate(self) -> None:
        self.tele.record("http", "answer_batch", "2 questions", "",
                         detail={"count": 2, "types": ["concept", "related"]})
        stats = self.tele.stats()
        self.assertEqual(stats["batch_calls"], 1)
        self.assertEqual(stats["batch_answers"], 2)
        self.assertEqual(stats["batch_by_type"]["concept"], 1)
        self.assertGreater(stats["hit_rate"], 0)

    def test_gap_aggregation(self) -> None:
        for _ in range(3):
            self.tele.record("mcp", "mcai_answer", "什么是元宇宙", "related")
        gaps = self.tele.gaps()
        self.assertEqual(gaps[0]["count"], 3)


class ManifestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        corpus = load_corpus(ROOT / "config" / "corpus.json")
        curated = load_config(ROOT / "config" / "curated.json")
        cls.kb = build(corpus, curated, None, load(ROOT / "config" / "disambiguation.json"))
        cls.work = Path(__file__).parent / "_work_site"
        shutil.rmtree(cls.work, ignore_errors=True)
        site.build_site(cls.kb, cls.work / "dist")

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.work, ignore_errors=True)

    def test_well_known_files(self) -> None:
        mcp = json.loads((self.work / "dist" / ".well-known" / "mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(len(mcp["tools"]), 5)
        self.assertEqual(mcp["transport"]["type"], "stdio")
        agent = json.loads((self.work / "dist" / ".well-known" / "agent.json").read_text(encoding="utf-8"))
        self.assertTrue(agent["skills"])
        api = json.loads((self.work / "dist" / "openapi.json").read_text(encoding="utf-8"))
        self.assertIn("/answer", api["paths"])

    def test_campaign_block_rendered(self) -> None:
        page = (self.work / "dist" / "concepts" / "meta-consciousness.html").read_text(encoding="utf-8")
        self.assertIn("常见误解（阶段性）", page)
        self.assertIn("不属于术语定义", page)

    def test_schema_disambiguating_description(self) -> None:
        page = (self.work / "dist" / "concepts" / "meta-consciousness.html").read_text(encoding="utf-8")
        self.assertIn("disambiguatingDescription", page)

    def test_manifest_builders(self) -> None:
        mcp = manifest.mcp_manifest(self.kb, self.kb.project)
        self.assertIn("http", mcp)
        card = manifest.agent_card(self.kb, self.kb.project)
        self.assertEqual(card["capabilities"]["streaming"], False)


if __name__ == "__main__":
    unittest.main()
