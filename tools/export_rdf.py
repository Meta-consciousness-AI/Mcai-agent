# -*- coding: utf-8 -*-
"""把知识库导出为 RDF：mcai-knowledge.ttl（Turtle）与 .nt（N-Triples）。

不依赖第三方库：输出的是 N-Triples 子集，Turtle 文件由同样的三元组加前缀组成。
命名空间：https://w3id.org/mcai/
"""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "data" / "kb.json"
OUT_DIR = ROOT / "dist" / "dataset"

BASE = "https://w3id.org/mcai/"
PREFIXES = {
    "mcai": BASE,
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dcterms": "http://purl.org/dc/terms/",
    "prov": "http://www.w3.org/ns/prov#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "owl": "http://www.w3.org/2002/07/owl#",
}

triples = []  # (subject, predicate, object_repr)


def esc(s: str) -> str:
    return (s.replace("\\", "\\\\").replace('"', '\\"')
             .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t"))


def lit(s: str, lang: str = "zh") -> str:
    return f'"{esc(s)}"@{lang}' if lang else f'"{esc(s)}"'


def iri(u: str) -> str:
    return f"<{u}>"


def concept_uri(slug: str) -> str:
    return BASE + "concept/" + quote(slug, safe="-_.~")


def doc_uri(doc_id: str) -> str:
    return BASE + "document/" + quote(doc_id, safe="-_.~")


def category_uri(name: str) -> str:
    h = hashlib.md5(name.encode("utf-8")).hexdigest()[:10]
    return BASE + "category/" + h


def bnode(i: int) -> str:
    return f"_:b{i}"


def add(s, p, o):
    triples.append((s, p, o))


def main():
    data = json.loads(KB.read_text(encoding="utf-8"))
    concepts = data["concepts"]
    meta = data.get("meta", {}).get("project", {})

    scheme = iri(BASE + "scheme")
    add(iri(BASE + "ontology"), iri(PREFIXES["rdf"] + "type"), iri(PREFIXES["owl"] + "Ontology"))
    add(iri(BASE + "ontology"), iri(PREFIXES["rdfs"] + "label"), lit("元意识学说知识资产词表", "zh"))
    add(iri(BASE + "ontology"), iri(PREFIXES["rdfs"] + "label"), lit("MCAI Knowledge Assets Vocabulary", "en"))
    add(iri(BASE + "ontology"), iri(PREFIXES["dcterms"] + "license"), lit(meta.get("license", "CC BY-NC-SA 4.0")))

    add(scheme, iri(PREFIXES["rdf"] + "type"), iri(PREFIXES["skos"] + "ConceptScheme"))
    add(scheme, iri(PREFIXES["skos"] + "prefLabel"), lit("元意识学说标准词表", "zh"))
    add(scheme, iri(PREFIXES["skos"] + "prefLabel"), lit("MCAI Standard Terminology", "en"))

    cats = {}
    for c in concepts:
        cats.setdefault(c.get("category", ""), set()).add(c["slug"])

    for name, slugs in cats.items():
        cu = category_uri(name)
        add(iri(cu), iri(PREFIXES["rdf"] + "type"), iri(PREFIXES["skos"] + "Concept"))
        add(iri(cu), iri(PREFIXES["skos"] + "prefLabel"), lit(name, "zh"))
        add(iri(cu), iri(PREFIXES["skos"] + "inScheme"), scheme)

    b = 0
    for c in concepts:
        cu = concept_uri(c["slug"])
        add(iri(cu), iri(PREFIXES["rdf"] + "type"), iri(PREFIXES["skos"] + "Concept"))
        add(iri(cu), iri(PREFIXES["skos"] + "inScheme"), scheme)
        add(iri(cu), iri(PREFIXES["skos"] + "prefLabel"), lit(c["term"], "zh"))
        if c.get("en"):
            add(iri(cu), iri(PREFIXES["skos"] + "altLabel"), lit(c["en"], "en"))
        for a in c.get("aliases") or []:
            add(iri(cu), iri(PREFIXES["skos"] + "altLabel"), lit(a, "zh"))
        if c.get("definition"):
            add(iri(cu), iri(PREFIXES["skos"] + "definition"), lit(c["definition"], "zh"))
        add(iri(cu), iri(PREFIXES["skos"] + "broader"), iri(category_uri(c.get("category", ""))))
        if c.get("parent_id"):
            add(iri(cu), iri(PREFIXES["skos"] + "broader"), iri(concept_uri(c["parent_id"])))
        if c.get("short_definition"):
            add(iri(cu), iri(BASE + "shortDefinition"), lit(c["short_definition"], "zh"))
        if c.get("definition_type"):
            add(iri(cu), iri(BASE + "definitionType"), lit(c["definition_type"], ""))
        if c.get("editor_note"):
            add(iri(cu), iri(BASE + "editorNote"), lit(c["editor_note"], "zh"))

        for src in c.get("sources") or []:
            b += 1
            sn = bnode(b)
            add(iri(cu), iri(PREFIXES["dcterms"] + "source"), sn)
            add(sn, iri(PREFIXES["rdf"] + "type"), iri(PREFIXES["prov"] + "Entity"))
            if src.get("doc_title"):
                add(sn, iri(PREFIXES["dcterms"] + "title"), lit(src["doc_title"], "zh"))
            if src.get("section"):
                add(sn, iri(PREFIXES["dcterms"] + "isPartOf"), lit(src["section"], "zh"))
            if src.get("quote"):
                add(sn, iri(BASE + "quote"), lit(src["quote"], "zh"))
            if src.get("location"):
                add(sn, iri(BASE + "location"), lit(src["location"], ""))
            if src.get("edition"):
                add(sn, iri(BASE + "edition"), lit(src["edition"], "zh"))
            if src.get("doc_id"):
                add(sn, iri(PREFIXES["prov"] + "wasDerivedFrom"), iri(doc_uri(src["doc_id"])))
            if src.get("char_start") is not None:
                add(sn, iri(BASE + "charStart"), f'"{int(src["char_start"])}"^^<http://www.w3.org/2001/XMLSchema#integer>')
            if src.get("char_end") is not None:
                add(sn, iri(BASE + "charEnd"), f'"{int(src["char_end"])}"^^<http://www.w3.org/2001/XMLSchema#integer>')

        for r in c.get("relations") or []:
            if not r.get("target_id"):
                continue
            b += 1
            rn = bnode(b)
            add(iri(cu), iri(BASE + "relation"), rn)
            add(rn, iri(PREFIXES["rdf"] + "type"), iri(BASE + "Relation"))
            add(rn, iri(BASE + "target"), iri(concept_uri(r["target_id"])))
            if r.get("type"):
                add(rn, iri(BASE + "relationType"), lit(r["type"], "zh"))
            if r.get("tier"):
                add(rn, iri(BASE + "tier"), lit(r["tier"], ""))
            if r.get("evidence"):
                add(rn, iri(BASE + "evidence"), lit(r["evidence"], "zh"))

    # 文档节点
    docs = {}
    for c in concepts:
        for src in c.get("sources") or []:
            if src.get("doc_id"):
                docs.setdefault(src["doc_id"], src.get("doc_title", ""))
    for doc_id, title in docs.items():
        du = doc_uri(doc_id)
        add(iri(du), iri(PREFIXES["rdf"] + "type"), iri(PREFIXES["dcterms"] + "BibliographicResource"))
        add(iri(du), iri(PREFIXES["dcterms"] + "title"), lit(title, "zh"))

    # 输出
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def render(o):
        if o.startswith("<") or o.startswith("_:"):
            return o
        if o.startswith('"'):
            return o
        return iri(PREFIXES[o.split(":")[0]] + o.split(":", 1)[1])

    nt_lines, ttl_lines = [], []
    for s, p, o in triples:
        ss = render(s) if not (s.startswith("<") or s.startswith("_:")) else s
        pp = render(p) if not (p.startswith("<") or p.startswith("_:")) else p
        oo = render(o) if not (o.startswith("<") or o.startswith("_:")) else o
        nt_lines.append(f"{ss} {pp} {oo} .")

    ttl_lines = [f"@prefix {k}: <{v}> ." for k, v in PREFIXES.items()]
    ttl_lines.append("")
    ttl_lines.extend(nt_lines)

    (OUT_DIR / "mcai-knowledge.nt").write_text("\n".join(nt_lines) + "\n", encoding="utf-8")
    (OUT_DIR / "mcai-knowledge.ttl").write_text("\n".join(ttl_lines) + "\n", encoding="utf-8")

    # 自检
    bad = [l for l in nt_lines if not re.match(r'^(<[^>]+>|_:[A-Za-z0-9]+) <[^>]+> (.+?) \.$', l)]
    print("triples", len(nt_lines), "bad", len(bad))
    print("concepts", len(concepts), "relations", sum(len(c.get("relations") or []) for c in concepts))
    print("wrote", OUT_DIR / "mcai-knowledge.ttl")
    if bad:
        print("BAD SAMPLE:", bad[:2])


if __name__ == "__main__":
    main()
