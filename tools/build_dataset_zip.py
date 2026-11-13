# -*- coding: utf-8 -*-
"""打包 Zenodo 数据集 v1.2。"""
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "dist" / "dataset"
OUT = ROOT / "dist_pkg" / "mcai-knowledge-dataset-v1.2.zip"

FILES = [
    ("README.md", ROOT / "docs" / "dataset-README.md"),
    ("concepts.csv", SRC / "concepts.csv"),
    ("concepts.jsonl", SRC / "concepts.jsonl"),
    ("evidence.jsonl", SRC / "evidence.jsonl"),
    ("faq.jsonl", SRC / "faq.jsonl"),
    ("knowledge-graph.json", SRC / "knowledge-graph.json"),
    ("provenance.jsonl", SRC / "provenance.jsonl"),
    ("relations.jsonl", SRC / "relations.jsonl"),
    ("sft.jsonl", SRC / "sft.jsonl"),
    ("mcai-knowledge.ttl", SRC / "mcai-knowledge.ttl"),
    ("mcai-knowledge.nt", SRC / "mcai-knowledge.nt"),
    ("dataset-card.md", SRC / "dataset-card.md"),
]


def main():
    missing = [str(p) for _, p in FILES if not p.exists()]
    if missing:
        raise SystemExit("missing: " + ", ".join(missing))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for name, path in FILES:
            z.write(path, arcname=name)
    h = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print("wrote", OUT, OUT.stat().st_size, "bytes")
    print("sha256", h)
    with zipfile.ZipFile(OUT) as z:
        for n in z.namelist():
            print(" ", n, z.getinfo(n).file_size)


if __name__ == "__main__":
    main()
