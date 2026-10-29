# -*- coding: utf-8 -*-
"""上线工具测试：设置站点地址、远程体检。"""
import json
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai import deploy, workspace  # noqa: E402


class SetUrlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.work = Path(__file__).parent / "_work_deploy"
        shutil.rmtree(self.work, ignore_errors=True)
        workspace.init_workspace(self.work)
        cfg_path = self.work / "config" / "corpus.json"
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        cfg["project"]["site_url"] = "http://127.0.0.1:8787"
        cfg["keywords"] = ["元意识"]
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.work, ignore_errors=True)

    def test_set_url(self) -> None:
        info = deploy.set_site_url(self.work, "https://kb.example.com/")
        self.assertEqual(info["new"], "https://kb.example.com")
        cfg = json.loads((self.work / "config" / "corpus.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["project"]["site_url"], "https://kb.example.com")
        self.assertEqual(cfg["keywords"], ["元意识"])  # 其他字段不受影响

    def test_rejects_bad_scheme(self) -> None:
        with self.assertRaises(ValueError):
            deploy.set_site_url(self.work, "kb.example.com")

    def test_token_shape(self) -> None:
        token = deploy.new_token()
        self.assertGreaterEqual(len(token), 24)
        self.assertNotEqual(token, deploy.new_token())


class DoctorTest(unittest.TestCase):
    def test_unreachable_returns_failures(self) -> None:
        checks = deploy.doctor("http://127.0.0.1:9", timeout=1)
        self.assertTrue(checks)
        self.assertTrue(all("name" in c and "ok" in c for c in checks))
        by_name = {c["name"]: c for c in checks}
        self.assertFalse(by_name["health"]["ok"])
        self.assertFalse(by_name["answer"]["ok"])
        self.assertTrue(any(c.get("hint") for c in checks))


if __name__ == "__main__":
    unittest.main()
