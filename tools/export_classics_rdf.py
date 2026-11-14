# -*- coding: utf-8 -*-
"""把三部经典（道德经 / 孙子 / 荀子）打包为 RDF。

仅内部资产：命名空间用 urn:mcai:classic:*，不占用 w3id，不对外发布。
"""
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcai.verify import verify  # noqa: E402
from tools.export_rdf import export  # noqa: E402

WORKS = {
    "daodejing": "道德经",
    "sunzi": "孙子兵法",
    "xunzi": "荀子·正名",
}
OUT = ROOT / "dist_pkg" / "classics-rdf"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main():
    manifest = {"generated": date.today().isoformat(), "published": False,
                "namespace": "urn:mcai:classic:", "works": []}
    for work, label in WORKS.items():
        home = ROOT / "workspaces" / work
        kb_path = home / "data" / "kb.json"
        if not kb_path.exists():
            print(f"SKIP {work}: no kb.json")
            continue
        kb = json.loads(kb_path.read_text(encoding="utf-8"))
        stats = kb["meta"]["stats"]
        thin = sum(1 for c in kb["concepts"] if c.get("status") == "thin")
        vs = verify(kb_path, home / "config" / "corpus.json")
        result = export(
            kb_path, OUT, f"urn:mcai:classic:{work}:", work,
            ontology_label_zh=f"{label}知识资产词表",
            ontology_label_en=f"{label} Knowledge Assets Vocabulary",
            scheme_label_zh=f"{label}标准词表",
            scheme_label_en=f"{label} Terminology",
        )
        entry = {
            "work": work,
            "label": label,
            "concepts": stats["concepts"],
            "faqs": stats["faqs"],
            "relations": stats["relations"],
            "thin": thin,
            "thin_ratio": round(thin / stats["concepts"], 3) if stats["concepts"] else 0,
            "license": kb["meta"]["project"].get("license", ""),
            "triples": result["triples"],
            "bad_triples": result["bad"],
            "verify_ok": vs["ok"],
            "verify": vs["stats"],
            "ttl_sha256": sha256(Path(result["ttl"])),
            "nt_sha256": sha256(Path(result["nt"])),
            "files": [str(Path(result["ttl"]).relative_to(ROOT)),
                      str(Path(result["nt"]).relative_to(ROOT))],
        }
        manifest["works"].append(entry)
        print(f"{work}: {result['triples']} triples, thin {thin}/{stats['concepts']}, verify {vs['ok']}")

    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT / "manifest.json")


if __name__ == "__main__":
    main()
