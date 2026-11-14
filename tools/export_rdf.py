# -*- coding: utf-8 -*-
"""知识库导出 RDF（Turtle + N-Triples），不依赖第三方库。

默认导出元意识知识库：
    python tools/export_rdf.py

也可指定任意工作区与命名空间：
    python tools/export_rdf.py --kb path/to/data/kb.json --base urn:mcai:classic:demo: \
        --out dist_pkg/demo --name demo
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent

PREFIXES = {
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dcterms": "http://purl.org/dc/terms/",
    "prov": "http://www.w3.org/ns/prov#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "owl": "http://www.w3.org/2002/07/owl#",
}


def esc(s: str) -> str:
    return (s.replace("\\", "\\\\").replace('"', '\\"')
             .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t"))


def lit(s: str, lang: str = "zh") -> str:
    return f'"{esc(s)}"@{lang}' if lang else f'"{esc(s)}"'


def iri(u: str) -> str:
    return f"<{u}>"


class Builder:
    def __init__(self, base: str, prefix: str = "mcai"):
        self.base = base
        self.prefix = prefix
        self.triples = []

    def concept_uri(self, slug: str) -> str:
        return self.base + "concept/" + quote(slug, safe="-_.~")

    def doc_uri(self, doc_id: str) -> str:
        return self.base + "document/" + quote(doc_id, safe="-_.~")

    def category_uri(self, name: str) -> str:
        h = hashlib.md5(name.encode("utf-8")).hexdigest()[:10]
        return self.base + "category/" + h

    def term(self, local: str) -> str:
        return self.prefix + ":" + local

    def add(self, s, p, o):
        self.triples.append((s, p, o))


def build(kb: dict, base: str, prefix: str = "mcai",
          ontology_label_zh: str = "", ontology_label_en: str = "",
          scheme_label_zh: str = "", scheme_label_en: str = "") -> Builder:
    b = Builder(base, prefix)
    concepts = kb.get("concepts", [])
    meta = kb.get("meta", {}).get("project", {})
    brand = meta.get("brand") or meta.get("name") or "知识库"

    b.add(iri(base + "ontology"), iri(PREFIXES["rdf"] + "type"), iri(PREFIXES["owl"] + "Ontology"))
    b.add(iri(base + "ontology"), iri(PREFIXES["rdfs"] + "label"),
          lit(ontology_label_zh or f"{brand}知识资产词表", "zh"))
    b.add(iri(base + "ontology"), iri(PREFIXES["rdfs"] + "label"),
          lit(ontology_label_en or f"{brand} Knowledge Assets Vocabulary", "en"))
    b.add(iri(base + "ontology"), iri(PREFIXES["dcterms"] + "license"),
          lit(meta.get("license", "")))

    scheme = iri(base + "scheme")
    b.add(scheme, iri(PREFIXES["rdf"] + "type"), iri(PREFIXES["skos"] + "ConceptScheme"))
    b.add(scheme, iri(PREFIXES["skos"] + "prefLabel"), lit(scheme_label_zh or f"{brand}标准词表", "zh"))
    b.add(scheme, iri(PREFIXES["skos"] + "prefLabel"), lit(scheme_label_en or f"{brand} Terminology", "en"))

    cats = {}
    for c in concepts:
        cats.setdefault(c.get("category", ""), set()).add(c["slug"])
    for name, _slugs in cats.items():
        cu = b.category_uri(name)
        b.add(iri(cu), iri(PREFIXES["rdf"] + "type"), iri(PREFIXES["skos"] + "Concept"))
        b.add(iri(cu), iri(PREFIXES["skos"] + "prefLabel"), lit(name, "zh"))
        b.add(iri(cu), iri(PREFIXES["skos"] + "inScheme"), scheme)

    n = 0
    for c in concepts:
        cu = b.concept_uri(c["slug"])
        b.add(iri(cu), iri(PREFIXES["rdf"] + "type"), iri(PREFIXES["skos"] + "Concept"))
        b.add(iri(cu), iri(PREFIXES["skos"] + "inScheme"), scheme)
        b.add(iri(cu), iri(PREFIXES["skos"] + "prefLabel"), lit(c["term"], "zh"))
        if c.get("en"):
            b.add(iri(cu), iri(PREFIXES["skos"] + "altLabel"), lit(c["en"], "en"))
        for a in c.get("aliases") or []:
            b.add(iri(cu), iri(PREFIXES["skos"] + "altLabel"), lit(a, "zh"))
        if c.get("definition"):
            b.add(iri(cu), iri(PREFIXES["skos"] + "definition"), lit(c["definition"], "zh"))
        b.add(iri(cu), iri(PREFIXES["skos"] + "broader"), iri(b.category_uri(c.get("category", ""))))
        if c.get("parent_id"):
            b.add(iri(cu), iri(PREFIXES["skos"] + "broader"), iri(b.concept_uri(c["parent_id"])))
        if c.get("short_definition"):
            b.add(iri(cu), iri(base + "shortDefinition"), lit(c["short_definition"], "zh"))
        if c.get("definition_type"):
            b.add(iri(cu), iri(base + "definitionType"), lit(c["definition_type"], ""))
        if c.get("editor_note"):
            b.add(iri(cu), iri(base + "editorNote"), lit(c["editor_note"], "zh"))

        for src in c.get("sources") or []:
            n += 1
            sn = f"_:b{n}"
            b.add(iri(cu), iri(PREFIXES["dcterms"] + "source"), sn)
            b.add(sn, iri(PREFIXES["rdf"] + "type"), iri(PREFIXES["prov"] + "Entity"))
            if src.get("doc_title"):
                b.add(sn, iri(PREFIXES["dcterms"] + "title"), lit(src["doc_title"], "zh"))
            if src.get("section"):
                b.add(sn, iri(PREFIXES["dcterms"] + "isPartOf"), lit(src["section"], "zh"))
            if src.get("quote"):
                b.add(sn, iri(base + "quote"), lit(src["quote"], "zh"))
            if src.get("location"):
                b.add(sn, iri(base + "location"), lit(src["location"], ""))
            if src.get("edition"):
                b.add(sn, iri(base + "edition"), lit(src["edition"], "zh"))
            if src.get("doc_id"):
                b.add(sn, iri(PREFIXES["prov"] + "wasDerivedFrom"), iri(b.doc_uri(src["doc_id"])))
            if src.get("char_start") is not None:
                b.add(sn, iri(base + "charStart"),
                      f'"{int(src["char_start"])}"^^<{PREFIXES["xsd"]}integer>')
            if src.get("char_end") is not None:
                b.add(sn, iri(base + "charEnd"),
                      f'"{int(src["char_end"])}"^^<{PREFIXES["xsd"]}integer>')

        for r in c.get("relations") or []:
            if not r.get("target_id"):
                continue
            n += 1
            rn = f"_:b{n}"
            b.add(iri(cu), iri(base + "relation"), rn)
            b.add(rn, iri(PREFIXES["rdf"] + "type"), iri(base + "Relation"))
            b.add(rn, iri(base + "target"), iri(b.concept_uri(r["target_id"])))
            if r.get("type"):
                b.add(rn, iri(base + "relationType"), lit(r["type"], "zh"))
            if r.get("tier"):
                b.add(rn, iri(base + "tier"), lit(r["tier"], ""))
            if r.get("evidence"):
                b.add(rn, iri(base + "evidence"), lit(r["evidence"], "zh"))

    docs = {}
    for c in concepts:
        for src in c.get("sources") or []:
            if src.get("doc_id"):
                docs.setdefault(src["doc_id"], src.get("doc_title", ""))
    for doc_id, title in docs.items():
        du = b.doc_uri(doc_id)
        b.add(iri(du), iri(PREFIXES["rdf"] + "type"), iri(PREFIXES["dcterms"] + "BibliographicResource"))
        b.add(iri(du), iri(PREFIXES["dcterms"] + "title"), lit(title, "zh"))
    return b


def render(b: Builder, base: str, name: str):
    def one(o):
        if o.startswith("<") or o.startswith("_:") or o.startswith('"'):
            return o
        return iri(PREFIXES[o.split(":")[0]] + o.split(":", 1)[1])

    nt = [f"{one(s)} {one(p)} {one(o)} ." for s, p, o in b.triples]
    prefixes = {"mcai": base}
    prefixes.update({k: v for k, v in PREFIXES.items() if k != "rdf"})
    ttl = [f"@prefix {k}: <{v}> ." for k, v in prefixes.items()]
    ttl.append("")
    ttl.extend(nt)
    return nt, ttl


def export(kb_path: Path, out_dir: Path, base: str, name: str, prefix: str = "mcai",
           ontology_label_zh: str = "", ontology_label_en: str = "",
           scheme_label_zh: str = "", scheme_label_en: str = "") -> dict:
    kb = json.loads(Path(kb_path).read_text(encoding="utf-8"))
    b = build(kb, base, prefix, ontology_label_zh, ontology_label_en, scheme_label_zh, scheme_label_en)
    nt, ttl = render(b, base, name)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    nt_path = out_dir / f"{name}.nt"
    ttl_path = out_dir / f"{name}.ttl"
    nt_path.write_text("\n".join(nt) + "\n", encoding="utf-8")
    ttl_path.write_text("\n".join(ttl) + "\n", encoding="utf-8")
    bad = [line for line in nt if not re.match(r'^(<[^>]+>|_:[A-Za-z0-9]+) <[^>]+> (.+?) \.$', line)]
    return {
        "name": name,
        "triples": len(nt),
        "bad": len(bad),
        "concepts": len(kb.get("concepts", [])),
        "ttl": str(ttl_path),
        "nt": str(nt_path),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", default=str(ROOT / "data" / "kb.json"))
    ap.add_argument("--out", default=str(ROOT / "dist" / "dataset"))
    ap.add_argument("--base", default="https://w3id.org/mcai/")
    ap.add_argument("--name", default="mcai-knowledge")
    ap.add_argument("--prefix", default="mcai")
    args = ap.parse_args()
    result = export(Path(args.kb), Path(args.out), args.base, args.name, args.prefix)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
