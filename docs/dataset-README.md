# MCAI Knowledge Base — dataset v1.2

Structured knowledge assets for the Meta-Consciousness Theory (元意识学说):
64 term definitions, 122 curated Q&A pairs, 270 typed relations, and 213 source
quotations. Every definition is linked to a document, a section, a character range,
and an edition.

Provided as JSONL, CSV, JSON, RDF/Turtle, and N-Triples. Suitable for retrieval-augmented
generation (RAG), terminology consistency checks, and instruction tuning.

## Files

| File | Content |
|---|---|
| `concepts.jsonl` | 64 concepts with definitions, aliases, categories, provenance |
| `concepts.csv` | same, tabular form |
| `faq.jsonl` | 122 curated question–answer pairs |
| `relations.jsonl` | 270 typed relations between concepts |
| `provenance.jsonl` | source quotations with character ranges |
| `evidence.jsonl` | supporting evidence passages |
| `knowledge-graph.json` | graph export (nodes and edges) |
| `mcai-knowledge.ttl` | RDF/Turtle export, SKOS + PROV + Dublin Core |
| `mcai-knowledge.nt` | N-Triples export of the same triples |
| `dataset-card.md` | dataset card |
| `README.md` | this file |

## RDF namespace

- Vocabulary: `https://w3id.org/mcai/ontology`
- Scheme: `https://w3id.org/mcai/scheme`
- Concepts: `https://w3id.org/mcai/concept/{slug}`

## License

Content: CC BY-NC-SA 4.0. Code: MIT.

## Cite

DOI (all versions): 10.5281/zenodo.23789330
Version DOI: 10.5281/zenodo.23836789
