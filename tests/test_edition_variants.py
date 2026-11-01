import unittest

from mcai import extract
from mcai.corpus import Block, Corpus, Document

PROJECT = {
    "name": "测试库", "brand": "测试", "org": "测试组织",
    "version": "0.1.0", "site_url": "http://localhost", "license": "CC0",
}

CURATED = {
    "english": {}, "categories": {"测试": ["测试词"]},
    "term_aliases": {}, "core_loop": [], "seed_faqs": [], "extra_concepts": [],
}


def make_corpus(docs: list[tuple[str, str, str, str]]) -> Corpus:
    """docs: (doc_id, title, edition, term_line)"""
    documents = []
    for idx, (doc_id, title, edition, line) in enumerate(docs):
        block = Block(doc_id, title, 0, line, "Normal", (), "l1")
        documents.append(Document(
            doc_id=doc_id, title=title, path=f"{doc_id}.txt",
            kind="glossary", priority=100 - idx, edition=edition, blocks=[block],
        ))
    return Corpus(project=PROJECT, keywords=[], term_blacklist=[], slugs={}, documents=documents)


class EditionVariantTest(unittest.TestCase):
    def test_different_editions_coexist(self):
        corpus = make_corpus([
            ("jia", "甲本", "甲本", "测试词：这是甲本给出的一个较长定义，用于验证版本并存。"),
            ("yi", "乙本", "乙本", "测试词：这是乙本完全不同的另一种较长表述，字句并不相同。"),
        ])
        c = extract.build(corpus, CURATED).by_term["测试词"]
        self.assertEqual(len(c.sources), 2)
        self.assertEqual(len(c.edition_variants), 1)
        self.assertNotEqual(c.status, "conflict")
        self.assertEqual({s.edition for s in c.sources}, {"甲本", "乙本"})

    def test_same_edition_still_conflicts(self):
        corpus = make_corpus([
            ("a", "同本一", "同一版本",
             "测试词：用于指称第一种对象，强调起源、结构与边界，讨论其在自然领域中的位置，并涉及历史脉络与分类标准。"),
            ("b", "同本二", "同一版本",
             "测试词：表示一种操作方法，关注步骤、次序与结果，不涉及对象起源。"),
        ])
        c = extract.build(corpus, CURATED).by_term["测试词"]
        self.assertEqual(c.status, "conflict")
        self.assertTrue(c.variants)


if __name__ == "__main__":
    unittest.main()
