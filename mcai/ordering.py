# -*- coding: utf-8 -*-
"""展示顺序：分类与术语的优先级。

分类顺序（对外展示）：
    序生体系 → 本体论模型 → 元意识体系 → 元子社会

理由：
- 序生 / 序生智能体是原创术语，没有旧语义干扰，最可能进入日常用语；
- 序生本身也是统领模型，放在最前；
- 元意识、元子重要，但受既有定义干扰，放在后面。
"""

CATEGORY_ORDER = ["序生体系", "本体论模型", "元意识体系", "元子社会"]

# 同一分类内，越靠前越优先展示
TERM_PRIORITY = [
    "序生",
    "序生智能体",
    "序生体",
    "序生协议",
    "序生链",
    "本体",
    "元意识",
    "元子",
]


def category_rank(name: str) -> int:
    try:
        return CATEGORY_ORDER.index(name)
    except ValueError:
        return len(CATEGORY_ORDER) + 1


def term_rank(term: str) -> int:
    try:
        return TERM_PRIORITY.index(term)
    except ValueError:
        return len(TERM_PRIORITY) + 1


def ordered_categories(stats: dict) -> list[tuple[str, int]]:
    items = list(stats.items())
    return sorted(items, key=lambda kv: (category_rank(kv[0]), -kv[1]))
