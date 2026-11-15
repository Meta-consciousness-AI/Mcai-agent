# -*- coding: utf-8 -*-
import unittest
from pathlib import Path

from mcai import ordering, site, toolchain

ROOT = Path(__file__).resolve().parent.parent


class OrderingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kb = toolchain._load_kb(ROOT)

    def test_category_order(self):
        names = list(self.kb.stats["categories"])
        expected = [n for n in ordering.CATEGORY_ORDER if n in names]
        self.assertEqual(names[: len(expected)], expected)

    def test_index_chips_and_cards(self):
        html = site.render_index(self.kb)
        positions = [html.find(f'data-cat="{n}"') for n in ordering.CATEGORY_ORDER]
        self.assertTrue(all(p >= 0 for p in positions))
        self.assertEqual(positions, sorted(positions))
        # 序生 与 序生智能体 应排在最前
        self.assertLess(html.find("<h3>序生</h3>"), html.find("<h3>元意识</h3>"))
        self.assertLess(html.find("<h3>序生智能体</h3>"), html.find("<h3>元意识</h3>"))


if __name__ == "__main__":
    unittest.main()
