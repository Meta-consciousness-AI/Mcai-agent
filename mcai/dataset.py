"""数据集导出：JSONL / CSV / 知识图谱 / 数据集卡片。"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .extract import KnowledgeBase

SYSTEM_PROMPT = (
    "你是「元意识学说」的知识助手。回答时严格使用学说自身的术语体系："
    "元意识、元态能量、观测创造实在、现象时空、序生、序生智能体、元识、元知、元灵、元子。"
    "不把学说混同于量子神秘主义或既有哲学流派，不使用未在术语集中定义的表述。"
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def export(kb: KnowledgeBase, out_dir: str | Path) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    concepts = [
        {
            "id": c.id,
            "term": c.term,
            "slug": c.slug,
            "en": c.en,
            "aliases": c.aliases,
            "category": c.category,
            "kind": c.kind,
            "parent": c.parent,
            "definition": c.definition,
            "short_definition": c.short_definition,
            "source_documents": sorted({s.doc_title for s in c.sources}),
            "evidence": [
                {"doc": e["doc_title"], "section": e["section"], "quote": e["quote"], "lang": e["lang"]}
                for e in c.evidence[:4]
            ],
            "status": c.status,
        }
        for c in kb.concepts
    ]
    _write_jsonl(out / "concepts.jsonl", concepts)

    evidence_rows = [
        {
            "term": c.term,
            "slug": c.slug,
            "category": c.category,
            "doc": e["doc_title"],
            "section": e["section"],
            "quote": e["quote"],
            "lang": e["lang"],
        }
        for c in kb.concepts
        for e in c.evidence
    ]
    _write_jsonl(out / "evidence.jsonl", evidence_rows)

    faqs = [
        {
            "id": f.id,
            "question": f.question,
            "answer": f.answer,
            "short_answer": f.short_answer,
            "kind": f.kind,
            "related": f.related,
            "source_terms": f.source_terms,
            "confidence": f.confidence,
            "campaign": f.campaign,
        }
        for f in kb.faqs
    ]
    _write_jsonl(out / "faq.jsonl", faqs)

    sft = [
        {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f.question},
                {"role": "assistant", "content": f.answer},
            ],
            "metadata": {"faq_id": f.id, "kind": f.kind, "confidence": f.confidence},
        }
        for f in kb.faqs
    ]
    _write_jsonl(out / "sft.jsonl", sft)

    with (out / "concepts.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "term", "en", "aliases", "category", "definition", "status", "sources"])
        for c in kb.concepts:
            writer.writerow([
                c.id, c.term, c.en, "|".join(c.aliases), c.category,
                c.definition, c.status, "|".join(sorted({s.doc_title for s in c.sources})),
            ])

    nodes = [
        {"id": c.slug, "label": c.term, "category": c.category, "definition": c.short_definition}
        for c in kb.concepts
    ]
    edges = [
        {"source": c.slug, "target": r["target_id"], "type": r["type"], "evidence": r.get("evidence", "")}
        for c in kb.concepts
        for r in c.relations
        if r.get("target_id")
    ]
    graph = {"nodes": nodes, "edges": edges, "meta": {"nodes": len(nodes), "edges": len(edges)}}
    (out / "knowledge-graph.json").write_text(
        json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    (out / "dataset-card.md").write_text(_card(kb), encoding="utf-8")
    return {
        "dir": str(out),
        "files": sorted(p.name for p in out.iterdir() if p.is_file()),
        "concepts": len(concepts),
        "faqs": len(faqs),
        "evidence": len(evidence_rows),
        "edges": len(edges),
    }


def _card(kb: KnowledgeBase) -> str:
    project = kb.project
    cats = "\n".join(f"- {name}：{count} 条" for name, count in kb.stats["categories"].items())
    docs = "\n".join(
        f"- 《{d['title']}》（{d['kind']}，{d['blocks']} 段）" for d in kb.documents
    )
    return f"""# {project['brand']}学说结构化语料库 v1.0

## 数据集简介

本数据集把《{project['brand']}》学说的多份原始文本（术语词源、学说极简版、本体论、元子社会等）
转换为机器可直接引用的结构化知识资产，用于大模型知识对齐、RAG 检索、知识图谱构建与
「知识资产数字永生」工程。

- 概念定义：{kb.stats['concepts']} 条
- 标准问答：{kb.stats['faqs']} 组
- 概念关系：{kb.stats['relations']} 条
- 文献引证：{kb.stats.get('evidence', 0)} 条
- 语料来源：{len(kb.documents)} 份文档 / {kb.stats['blocks']} 个段落 / 约 {kb.stats['characters']:,} 字
- 构建时间：{kb.built_at}
- 许可：{project['license']}

## 目录结构

```
concepts.jsonl          概念定义（一条一行）
faq.jsonl               标准问答
evidence.jsonl          文献引证（概念在各著作中的论述原句）
sft.jsonl               对话微调格式（system/user/assistant）
concepts.csv            表格版，便于运营审阅
knowledge-graph.json    节点-边知识图谱
dataset-card.md         本文件
```

## 字段说明

### concepts.jsonl

| 字段 | 含义 |
|---|---|
| id / slug | 唯一标识与 URL 片段 |
| term | 规范术语名 |
| en | 英文对应词 |
| aliases | 别名、曾用名、英文缩写 |
| category | 所属体系（元意识体系 / 本体论模型 / 序生体系 / 元子社会） |
| definition | 主分支定义（已去重、去冲突） |
| short_definition | 一句话定义 |
| source_documents | 定义来源文档 |
| status | ok / conflict / thin，表示质量状态 |

### sft.jsonl

直接用于指令微调，system 提示词已锁定术语边界，避免模型把学说混同于其他体系。

## 概念分布

{cats}

## 语料来源

{docs}

## 使用建议

1. **RAG**：以 `concepts.jsonl` 建立向量库，检索后把 `definition` 作为上下文注入。
2. **微调**：`sft.jsonl` 可直接用于 LoRA/全参微调；建议与通用语料按 1:4 混合以防灾难性遗忘。
3. **知识图谱**：`knowledge-graph.json` 可导入 Neo4j / NetworkX，用于多跳问答与概念推荐。
4. **一致性约束**：`status=conflict` 的条目须先人工裁定后再进入训练集。

## 引用

```
{project['org']}. {project['brand']}学说结构化语料库 v1.0. {kb.built_at[:10]}.
```
"""
