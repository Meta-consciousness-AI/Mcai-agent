# -*- coding: utf-8 -*-
import json
import shutil
import unittest
from pathlib import Path

from tools import prospect

ROOT = Path(__file__).resolve().parent.parent


class ProspectTest(unittest.TestCase):
    def setUp(self):
        self.tmp = ROOT / "tests" / "_tmp_prospect.jsonl"
        self.old = prospect.STORE
        prospect.STORE = self.tmp
        if self.tmp.exists():
            self.tmp.unlink()

    def tearDown(self):
        prospect.STORE = self.old
        shutil.rmtree(self.tmp.parent / "_tmp_prospect_dir", ignore_errors=True)
        if self.tmp.exists():
            self.tmp.unlink()

    def test_add_list_status(self):
        class A:
            name = "测试社"
            type = "出版社"
            city = "北京"
            url = ""
            email = "a@b.c"
            book = "《某书》"
            notes = ""
        prospect.cmd_add(A())
        rows = prospect.load()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "new")
        pid = rows[0]["id"]

        class S:
            id = pid
            to = "sent"
            note = ""
        prospect.cmd_status(S())
        rows = prospect.load()
        self.assertEqual(rows[0]["status"], "sent")
        self.assertTrue(rows[0]["contacted"])

    def test_stats(self):
        self.test_add_list_status()

        class Args:
            pass
        prospect.cmd_stats(Args())


if __name__ == "__main__":
    unittest.main()
