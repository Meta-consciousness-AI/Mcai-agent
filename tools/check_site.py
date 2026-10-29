# -*- coding: utf-8 -*-
"""站点自检：HTML 结构、JSON-LD 合法性、内部链接可达性。

用法：python tools/check_site.py
"""
import json
import sys
from pathlib import Path

from lxml import html

ROOT = Path(__file__).resolve().parent.parent
root = ROOT / "dist"
errors = []
warnings = []

if not root.exists():
    sys.exit("尚未构建：先运行 python run.py build")

pages = sorted(root.rglob("*.html"))
print(f"pages: {len(pages)}")

for page in pages:
    doc = html.parse(str(page)).getroot()
    is_internal = page.name == "dashboard.html"  # 内部观测台，不需要面向爬虫的标记
    if is_internal:
        continue
    if not doc.findtext(".//title"):
        errors.append(f"{page}: 缺少 <title>")
    if not doc.xpath('//meta[@name="description"]/@content'):
        warnings.append(f"{page}: 缺少 meta description")
    lds = doc.xpath('//script[@type="application/ld+json"]/text()')
    if not lds:
        errors.append(f"{page}: 缺少 JSON-LD")
    for i, block in enumerate(lds):
        try:
            data = json.loads(block)
            if "@context" not in data:
                errors.append(f"{page}: JSON-LD#{i} 缺少 @context")
        except json.JSONDecodeError as exc:
            errors.append(f"{page}: JSON-LD#{i} 解析失败 {exc}")
    for href in doc.xpath("//a/@href"):
        if href.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = href.lstrip("/")
        path = root / (target if target else "index.html")
        if target.endswith("/"):
            path = root / target / "index.html"
        if not path.exists():
            errors.append(f"{page}: 死链 {href}")

print(f"errors: {len(errors)}, warnings: {len(warnings)}")
for e in errors[:20]:
    print("  ERR", e)
for w in warnings[:10]:
    print("  WARN", w)

kb = json.loads((root / "kb.json").read_text(encoding="utf-8"))
need = ["元意识", "序生智能体", "观测创造实在", "元子", "本体"]
terms = {c["term"] for c in kb["concepts"]}
missing = [t for t in need if t not in terms]
print("missing core terms:", missing)
print("concepts:", len(kb["concepts"]), "faqs:", len(kb["faqs"]))
sys.exit(1 if (errors or missing) else 0)
