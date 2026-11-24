# -*- coding: utf-8 -*-
"""知识库冻结：默认构建不覆盖 kb.json；变更必须留痕，数量减少必须给理由。"""
import hashlib
import json
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai import changes, pipeline  # noqa: E402


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class KbFreezeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(__file__).resolve().parent / "_work_freeze"
        shutil.rmtree(self.tmp, ignore_errors=True)
        (self.tmp / "data").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "data" / "kb.json", self.tmp / "data" / "kb.json")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_build_keeps_kb(self) -> None:
        before = _sha(self.tmp / "data" / "kb.json")
        result = pipeline.rebuild(self.tmp)
        self.assertEqual(result["source"], "kb")
        self.assertEqual(before, _sha(self.tmp / "data" / "kb.json"))
        self.assertTrue((self.tmp / "dist" / "index.html").exists())
        self.assertEqual(result["concepts"], 65)

    def test_refuse_reduction_without_reason(self) -> None:
        kb = self.tmp / "data" / "kb.json"
        before = _sha(kb)
        with self.assertRaises(changes.ChangeError) as ctx:
            changes.apply(self.tmp, kind="relation", action="delete",
                          key="元识->元知", basis="测试")
        self.assertIn("拒绝", str(ctx.exception))
        self.assertEqual(before, _sha(kb), "被拒绝时知识库不得改动")
        self.assertFalse((self.tmp / "docs" / "变更记录" / "kb.jsonl").exists())

    def test_change_writes_log(self) -> None:
        entry = changes.apply(self.tmp, kind="term", action="update", key="元识",
                              field="definition", value="测试定义。",
                              reason="单元测试", basis="作者口述")
        self.assertTrue(entry["applied"])
        log = (self.tmp / "docs" / "变更记录" / "kb.jsonl").read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(log), 1)
        row = json.loads(log[0])
        for key in ("ts", "kind", "action", "key", "before", "after", "reason", "basis"):
            self.assertIn(key, row)
        self.assertEqual(row["after"], "测试定义。")
        payload = json.loads((self.tmp / "data" / "kb.json").read_text(encoding="utf-8"))
        term = next(c for c in payload["concepts"] if c["term"] == "元识")
        self.assertEqual(term["definition"], "测试定义。")


if __name__ == "__main__":
    unittest.main()
