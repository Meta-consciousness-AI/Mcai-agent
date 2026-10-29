# -*- coding: utf-8 -*-
"""抽检器与内容工厂测试（不联网，使用假模型）。"""
import json
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai import factory, knowledge, probe  # noqa: E402


class FakeLLM:
    model = "fake-model"
    available = True

    def __init__(self, text: str = "元意识是宇宙的本源，不可描述，经由观测创造实在。"):
        self.text = text
        self.calls = 0

    def chat(self, messages, temperature=0.0, max_tokens=700):
        self.calls += 1
        return self.text

    def stats(self):
        return {"model": self.model, "calls": self.calls, "prompt_tokens": 0, "completion_tokens": 0}


class ProbeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.kb = knowledge.load(ROOT)
        cls.work = Path(__file__).parent / "_work_probe"
        if cls.work.exists():
            shutil.rmtree(cls.work, ignore_errors=True)
        cls.work.mkdir(parents=True)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.work, ignore_errors=True)

    def test_build_questions(self) -> None:
        questions = probe.build_questions(self.kb, limit=6)
        self.assertEqual(len(questions), 6)
        kinds = {q["kind"] for q in questions}
        self.assertTrue(kinds <= {"definition", "contrast", "curated", "relation"})
        for q in questions:
            self.assertTrue(q["reference"])
            self.assertTrue(q["terms"])

    def test_score(self) -> None:
        s = probe.score("元意识是宇宙的本源", "元意识是宇宙的本源，不可描述。", ["元意识"])
        self.assertTrue(s["mention"])
        self.assertGreater(s["coverage"], 0.5)
        s2 = probe.score("我不知道", "元意识是宇宙的本源", ["元意识"])
        self.assertFalse(s2["mention"])
        self.assertLess(s2["coverage"], 0.2)

    def test_run_and_report(self) -> None:
        questions = probe.build_questions(self.kb, limit=3)
        llm = FakeLLM()
        result = probe.run(llm, self.kb, questions)
        self.assertEqual(result["questions"], 3)
        self.assertEqual(llm.calls, 6)
        self.assertIn("baseline", result["summary"])
        self.assertIn("grounded", result["summary"])
        report = probe.write_report(result, self.work)
        self.assertTrue(Path(report["json"]).exists())
        md = Path(report["markdown"]).read_text(encoding="utf-8")
        self.assertIn("模型抽检报告", md)
        self.assertIn("baseline", md)


class FactoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.kb = knowledge.load(ROOT)
        cls.work = Path(__file__).parent / "_work_factory"
        if cls.work.exists():
            shutil.rmtree(cls.work, ignore_errors=True)
        cls.work.mkdir(parents=True)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.work, ignore_errors=True)

    def test_offline_batch(self) -> None:
        concept = self.kb.by_term["元意识"]
        result = factory.generate_batch(None, self.kb, [concept], ["zhihu", "video"],
                                        self.work, offline=True)
        self.assertEqual(len(result["created"]), 2)
        path = self.work / "zhihu" / "meta-consciousness.md"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---"))
        self.assertIn("concept:", text)
        self.assertIn("元意识", text)

    def test_online_with_fake_llm(self) -> None:
        concept = self.kb.by_term["元意识"]
        llm = FakeLLM("元意识是宇宙的本源，不可描述。它经由观测创造实在，形成现象时空。"
                      "这段假文本用于验证生成链路，长度足够通过检查，不涉及具体理论细节。")
        result = factory.generate_batch(llm, self.kb, [concept], ["prompt"], self.work, offline=False)
        self.assertEqual(len(result["created"]), 1)
        self.assertEqual(llm.calls, 1)

    def test_check_flags_risky_claim(self) -> None:
        concept = self.kb.by_term["元意识"]
        status, issues = factory.check(concept, "元意识已被科学证明，是量子力学的终极答案。")
        self.assertEqual(status, "needs_review")
        self.assertTrue(any("科学" in i for i in issues))

    def test_unknown_format(self) -> None:
        self.assertNotIn("nope", factory.FORMATS)
        self.assertEqual(len(factory.FORMATS), 7)


if __name__ == "__main__":
    unittest.main()
