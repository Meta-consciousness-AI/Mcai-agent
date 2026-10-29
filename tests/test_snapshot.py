# -*- coding: utf-8 -*-
"""本地快照：创建、轮转、校验、恢复。"""
import json
import shutil
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai import snapshot, workspace  # noqa: E402


class SnapshotTest(unittest.TestCase):
    def setUp(self) -> None:
        self.work = Path(__file__).parent / "_work_snap"
        shutil.rmtree(self.work, ignore_errors=True)
        workspace.init_workspace(self.work)
        (self.work / "data").mkdir(exist_ok=True)
        (self.work / "data" / "kb.json").write_text(json.dumps({
            "meta": {"stats": {"concepts": 3, "faqs": 4, "relations": 2, "evidence": 1}},
            "concepts": [], "faqs": [],
        }), encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.work, ignore_errors=True)

    def test_create_and_manifest(self) -> None:
        result = snapshot.create(self.work, note="单元测试", keep=5, with_corpus=False)
        archive = Path(result["archive"])
        self.assertTrue(archive.exists())
        self.assertEqual(result["manifest"]["kb"]["concepts"], 3)
        with zipfile.ZipFile(archive) as zf:
            names = zf.namelist()
            manifest = json.loads(zf.read("snapshot-manifest.json").decode("utf-8"))
        self.assertIn("README.md", names)
        self.assertIn("snapshot-manifest.json", names)
        self.assertEqual(manifest["note"], "单元测试")

    def test_rotation(self) -> None:
        for i in range(3):
            snapshot.create(self.work, note=f"第{i}份", keep=2, with_corpus=False)
        archives = list((self.work / "backups").glob("snapshot-*.zip"))
        self.assertEqual(len(archives), 2)

    def test_list_and_verify(self) -> None:
        result = snapshot.create(self.work, note="列表示例", keep=5, with_corpus=False)
        rows = snapshot.list_snapshots(self.work)
        self.assertTrue(rows)
        self.assertEqual(rows[0]["note"], "列表示例")
        check = snapshot.verify(result["archive"])
        self.assertTrue(check["ok"])
        self.assertGreater(check["files"], 1)

    def test_restore(self) -> None:
        result = snapshot.create(self.work, note="恢复测试", keep=5, with_corpus=False)
        target = Path(__file__).parent / "_work_restore"
        shutil.rmtree(target, ignore_errors=True)
        restored = snapshot.restore(result["archive"], target)
        self.assertTrue(restored["ok"])
        self.assertTrue((target / "README.md").exists())
        self.assertTrue((target / "config" / "corpus.json").exists())

        # 非空目录必须显式 --force
        again = snapshot.restore(result["archive"], target)
        self.assertFalse(again["ok"])
        shutil.rmtree(target, ignore_errors=True)

    def test_missing_archive(self) -> None:
        check = snapshot.verify(self.work / "nope.zip")
        self.assertFalse(check["ok"])


if __name__ == "__main__":
    unittest.main()
