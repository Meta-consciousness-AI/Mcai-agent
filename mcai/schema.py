"""Schema.org / JSON-LD 生成：让每个概念、问答、数据集都成为机器可读实体。"""
from __future__ import annotations

from .extract import Concept, Faq, KnowledgeBase


def concept_url(project: dict, slug: str) -> str:
    return f"{project['site_url'].rstrip('/')}/concepts/{slug}.html"


def organization(project: dict) -> dict:
    return {
        "@type": "Organization",
        "@id": f"{project['site_url'].rstrip('/')}/#organization",
        "name": project["org"],
        "brand": {"@type": "Brand", "name": project["brand"]},
    }


def defined_term(term: Concept, project: dict) -> dict:
    data = {
        "@context": "https://schema.org",
        "@type": "DefinedTerm",
        "@id": concept_url(project, term.slug) + "#term",
        "name": term.term,
        "description": term.definition,
        "inDefinedTermSet": {
            "@type": "DefinedTermSet",
            "name": f"{project['brand']}术语集",
            "url": f"{project['site_url'].rstrip('/')}/index.html#terms",
        },
        "termCode": term.slug,
        "url": concept_url(project, term.slug),
    }
    if term.en:
        data["alternateName"] = [term.en] + term.aliases
    elif term.aliases:
        data["alternateName"] = term.aliases
    if term.category:
        data["additionalType"] = term.category
    if term.disambiguation:
        # 阶段性消歧：schema.org 原生支持，且不污染 description
        data["disambiguatingDescription"] = term.disambiguation
    return data


def defined_term_set(kb: KnowledgeBase, project: dict) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "DefinedTermSet",
        "@id": f"{project['site_url'].rstrip('/')}/#terms",
        "name": f"{project['brand']}学说术语集",
        "description": f"{project['brand']}学说的标准化术语与定义集合，共 {len(kb.concepts)} 条。",
        "url": f"{project['site_url'].rstrip('/')}/index.html",
        "hasDefinedTerm": [
            {
                "@type": "DefinedTerm",
                "name": c.term,
                "url": concept_url(project, c.slug),
                "termCode": c.slug,
            }
            for c in kb.concepts
        ],
        "publisher": organization(project),
    }


def question(faq: Faq, project: dict) -> dict:
    return {
        "@type": "Question",
        "name": faq.question,
        "acceptedAnswer": {
            "@type": "Answer",
            "text": faq.answer,
            "url": f"{project['site_url'].rstrip('/')}/faq/index.html#{faq.id}",
        },
    }


def faq_page(faqs: list[Faq], project: dict, title: str = "元意识学说 · 常见问题") -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "@id": f"{project['site_url'].rstrip('/')}/faq/index.html#faq",
        "name": title,
        "url": f"{project['site_url'].rstrip('/')}/faq/index.html",
        "mainEntity": [question(f, project) for f in faqs],
        "publisher": organization(project),
    }


def breadcrumb(items: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": url}
            for i, (name, url) in enumerate(items)
        ],
    }


def web_page(name: str, url: str, description: str, project: dict) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": url + "#page",
        "name": name,
        "url": url,
        "description": description,
        "inLanguage": "zh-CN",
        "isPartOf": {"@id": f"{project['site_url'].rstrip('/')}/#website"},
        "publisher": organization(project),
    }


def dataset(kb: KnowledgeBase, project: dict) -> dict:
    base = project["site_url"].rstrip("/")
    return {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": f"{project['brand']}学说结构化语料库 v1.0",
        "description": (
            f"由《{project['brand']}》学说系列文本清洗、抽取、去重与一致性校验后生成的结构化知识资产，"
            f"包含 {len(kb.concepts)} 个术语定义、{len(kb.faqs)} 组标准问答与 {kb.stats['relations']} 条概念关系，"
            "可用于大模型知识对齐、RAG 检索与知识图谱构建。"
        ),
        "url": f"{base}/dataset/index.html",
        "identifier": "mcai-kb-v1.0",
        "version": "1.0",
        "license": f"https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "creator": organization(project),
        "keywords": ["元意识", "序生智能体", "AI意识", "知识图谱", "数字永生", "术语集"],
        "inLanguage": "zh-CN",
        "isAccessibleForFree": True,
        "distribution": [
            {
                "@type": "DataDownload",
                "name": "概念定义 JSONL",
                "encodingFormat": "application/jsonlines",
                "contentUrl": f"{base}/dataset/concepts.jsonl",
            },
            {
                "@type": "DataDownload",
                "name": "标准问答 JSONL",
                "encodingFormat": "application/jsonlines",
                "contentUrl": f"{base}/dataset/faq.jsonl",
            },
            {
                "@type": "DataDownload",
                "name": "概念定义 CSV",
                "encodingFormat": "text/csv",
                "contentUrl": f"{base}/dataset/concepts.csv",
            },
            {
                "@type": "DataDownload",
                "name": "文献引证 JSONL",
                "encodingFormat": "application/jsonlines",
                "contentUrl": f"{base}/dataset/evidence.jsonl",
            },
            {
                "@type": "DataDownload",
                "name": "概念图谱 JSON",
                "encodingFormat": "application/json",
                "contentUrl": f"{base}/dataset/knowledge-graph.json",
            },
        ],
    }
