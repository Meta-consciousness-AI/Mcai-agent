# -*- coding: utf-8 -*-
"""工具链命令：validate（校验）与 package（打包）。"""
import json
import zipfile
from pathlib import Path

from . import dataset, quality
from .corpus import load_corpus
from .disambig import load as load_disambig
from .extract import build as build_kb
from .verify import render_text, verify


def _load_kb(home: Path):
    corpus = load_corpus(home / "config" / "corpus.json")
    curated_path = home / "config" / "curated.json"
    curated = json.loads(curated_path.read_text(encoding="utf-8")) if curated_path.exists() else {}
    overrides_path = home / "config" / "overrides.json"
    overrides = json.loads(overrides_path.read_text(encoding="utf-8")) if overrides_path.exists() else {}
    disambig = load_disambig(home / "config" / "disambiguation.json")
    return build_kb(corpus, curated, overrides, disambig)


def validate(home: Path) -> dict:
    kb_path = home / "data" / "kb.json"
    if not kb_path.exists():
        raise SystemExit("未找到 data/kb.json，请先运行 mcai build")
    report = verify(kb_path, home / "config" / "corpus.json")
    print(render_text(report))
    q = quality.inspect(home)
    counts = q["counts"]
    print(f"\n质量巡检：{'✅ 通过' if q['ok'] else '❌ 有问题'}"
          f"（错误 {counts['error']} · 警告 {counts['warn']}）")
    return {"verify": report, "quality": q, "ok": report["ok"] and q["ok"]}


def package(home: Path) -> dict:
    kb = _load_kb(home)
    out_dir = home / "dist" / "dataset"
    dataset.export(kb, out_dir)

    readme = home / "docs" / "dataset-README.md"
    if readme.exists():
        (out_dir / "README.md").write_text(readme.read_text(encoding="utf-8"), encoding="utf-8")

    kb_json = home / "data" / "kb.json"
    version = "0.0.0"
    if kb_json.exists():
        version = (json.loads(kb_json.read_text(encoding="utf-8"))
                   .get("meta", {}).get("project", {}).get("version", "0.0.0"))
    out = home / "dist_pkg" / f"mcai-knowledge-dataset-{version}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in out_dir.iterdir() if p.is_file())
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, arcname=p.name)
    return {"path": str(out), "version": version, "files": [p.name for p in files]}
