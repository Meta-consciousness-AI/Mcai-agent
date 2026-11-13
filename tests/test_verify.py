# -*- coding: utf-8 -*-
import json
import shutil
import unittest
from pathlib import Path

from mcai.verify import verify, render_text


class VerifyTest(unittest.TestCase):
    def setUp(self):
        d = Path(__file__).resolve().parent / '_tmp_verify'
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True, exist_ok=True)
        self.tmp = str(d)
        blocks = [
            {"doc_id": "doc1", "location": "p1", "text": "元意识是宇宙的本源，不可描述。"},
            {"doc_id": "doc1", "location": "p2", "text": "观测创造实在，这是运行逻辑。"},
        ]
        (d / "corpus.jsonl").write_text(
            "\n".join(json.dumps(b, ensure_ascii=False) for b in blocks) + "\n",
            encoding="utf-8")
        kb = {
            "concepts": [
                {"term": "元意识", "sources": [
                    {"doc_id": "doc1", "location": "p1",
                     "quote": "元意识是宇宙的本源", "char_start": 0, "char_end": 9, "origin": "corpus"},
                ]},
                {"term": "观测", "sources": [
                    {"doc_id": "doc1", "location": "p2",
                     "quote": "观测创造实在", "char_start": 99, "char_end": 105, "origin": "corpus"},
                ]},
                {"term": "人工", "sources": [
                    {"doc_id": "doc1", "location": "p2",
                     "quote": "不存在的句子", "origin": "corpus"},
                    {"doc_id": "doc9", "location": "p9",
                     "quote": "也找不到", "origin": "corpus"},
                    {"doc_id": "doc1", "location": "p1",
                     "quote": "编者补充", "origin": "curated"},
                ]},
            ]
        }
        (d / "kb.json").write_text(json.dumps(kb, ensure_ascii=False), encoding="utf-8")
        self.kb = d / "kb.json"
        self.corpus = d / "corpus.jsonl"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_counts_and_problems(self):
        report = verify(self.kb, self.corpus)
        s = report["stats"]
        self.assertEqual(s["total"], 5)
        self.assertEqual(s["curated"], 1)
        self.assertEqual(s["corpus_total"], 4)
        self.assertEqual(s["exact"], 2)
        self.assertEqual(s["offset_ok"], 1)
        kinds = {p["kind"] for p in report["problems"]}
        self.assertIn("offset_mismatch", kinds)
        self.assertIn("quote_not_in_block", kinds)
        self.assertIn("location_not_found", kinds)
        self.assertFalse(report["ok"])

    def test_render_contains_conclusion(self):
        text = render_text(verify(self.kb, self.corpus))
        self.assertIn("结论", text)
        self.assertIn("存在问题", text)


if __name__ == "__main__":
    unittest.main()
