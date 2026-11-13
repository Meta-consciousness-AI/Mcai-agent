# -*- coding: utf-8 -*-
import unittest
from pathlib import Path

from mcai import toolchain
from mcai.cli import build_parser

ROOT = Path(__file__).resolve().parent.parent


class ToolchainTest(unittest.TestCase):
    def test_validate_passes_on_repo(self):
        result = toolchain.validate(ROOT)
        self.assertTrue(result["ok"])
        self.assertEqual(result["verify"]["stats"]["normalized"], 0)

    def test_package_creates_zip(self):
        result = toolchain.package(ROOT)
        path = Path(result["path"])
        self.assertTrue(path.exists())
        self.assertGreater(path.stat().st_size, 1000)
        self.assertIn("concepts.jsonl", result["files"])

    def test_parser_has_commands(self):
        parser = build_parser()
        help_text = parser.format_help()
        for name in ["validate", "package", "all"]:
            self.assertIn(name, help_text)


if __name__ == "__main__":
    unittest.main()
