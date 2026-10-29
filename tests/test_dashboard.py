# -*- coding: utf-8 -*-
"""观测台渲染测试。"""
import json
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai import dashboard  # noqa: E402


class DashboardTest(unittest.TestCase):
    def test_render_real_workspace(self) -> None:
        path = dashboard.render(ROOT)
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        for needle in ("本地观测台", "调用趋势", "巡检时间线", "质量明细", "术语变更", "外部调用", "命令行调用"):
            self.assertIn(needle, text)

    def test_render_without_history(self) -> None:
        work = Path(__file__).parent / "_work_dash"
        shutil.rmtree(work, ignore_errors=True)
        (work / "dist").mkdir(parents=True)
        path = dashboard.render(work)
        text = path.read_text(encoding="utf-8")
        self.assertIn("还没有巡检记录", text)
        self.assertIn("暂无调用记录", text)
        shutil.rmtree(work, ignore_errors=True)

    def test_reflects_status(self) -> None:
        work = Path(__file__).parent / "_work_dash2"
        shutil.rmtree(work, ignore_errors=True)
        (work / "data").mkdir(parents=True)
        (work / "dist").mkdir(parents=True)
        (work / "data" / "status.json").write_text(json.dumps({
            "ok": True, "checked_at": "2026-01-01T00:00:00+08:00",
            "concepts": 7, "faqs": 9, "relations": 3, "evidence": 5,
            "server_ok": True, "rebuilt": False,
        }, ensure_ascii=False), encoding="utf-8")
        text = dashboard.render(work).read_text(encoding="utf-8")
        self.assertIn("7", text)
        self.assertIn("健康", text)
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
