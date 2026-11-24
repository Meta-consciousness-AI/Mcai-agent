# -*- coding: utf-8 -*-
"""从现有 data/kb.json 直接生成静态站点，不重新抽取语料。

用途：术语审校后只更新了 kb，不想因为重新抽取而覆盖修订。
等价于 `mcai build`（默认模式）：只写 dist/ 与数据集，不改 kb.json。
用法：python tools/build_site_from_kb.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai import pipeline  # noqa: E402


def main() -> int:
    result = pipeline.rebuild(ROOT, from_corpus=False)
    print(f"pages: {result['pages']}")
    print(f"out: {ROOT / 'dist'}")
    meta = pipeline.load_kb(ROOT).get("meta") or {}
    print("version:", (meta.get("project") or {}).get("version"))
    print("kb source: data/kb.json（未改写）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
