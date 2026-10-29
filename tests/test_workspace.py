# -*- coding: utf-8 -*-
"""工作区解析与初始化测试。"""
import json
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai import workspace  # noqa: E402


class WorkspaceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.work = Path(__file__).parent / "_work_ws"
        shutil.rmtree(self.work, ignore_errors=True)
        self.work.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.work, ignore_errors=True)

    def test_init_creates_config(self) -> None:
        result = workspace.init_workspace(self.work)
        cfg = self.work / "config" / "corpus.json"
        self.assertTrue(cfg.exists())
        data = json.loads(cfg.read_text(encoding="utf-8"))
        self.assertIn("corpus", data)
        self.assertIn("slugs", data)
        self.assertTrue((self.work / "config" / "curated.json").exists())
        self.assertTrue((self.work / "README.md").exists())
        self.assertTrue(result["created"])

    def test_init_idempotent(self) -> None:
        workspace.init_workspace(self.work)
        (self.work / "config" / "corpus.json").write_text('{"corpus": []}', encoding="utf-8")
        result = workspace.init_workspace(self.work)
        self.assertEqual(result["created"], [])
        self.assertTrue(result["skipped"])
        # 不覆盖已有配置
        self.assertEqual(
            json.loads((self.work / "config" / "corpus.json").read_text(encoding="utf-8")),
            {"corpus": []},
        )

    def test_resolve_home_explicit(self) -> None:
        workspace.init_workspace(self.work)
        self.assertEqual(workspace.resolve_home(str(self.work)).resolve(), self.work.resolve())

    def test_templates_have_no_absolute_key_path(self) -> None:
        template = ROOT / "mcai" / "templates" / "config" / "llm.json"
        data = json.loads(template.read_text(encoding="utf-8"))
        self.assertIn(data.get("key_path", ""), ("", None))


if __name__ == "__main__":
    unittest.main()
