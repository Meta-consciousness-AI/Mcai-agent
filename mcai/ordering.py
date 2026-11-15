# -*- coding: utf-8 -*-
"""展示顺序：分类、首页术语与同分类内的优先级。

分类顺序（对外展示，固定不变）：
    序生体系 → 本体论模型 → 元意识体系 → 元子社会

首页卡片顺序（按「逃逸概率」排）：
逃逸 = 术语离开学说、进入社会日常用语的可能性。
判断标准：
1. 没有旧定义与语义干扰（越新越好）；
2. 能独立成词、可脱离学说使用；
3. 与当下技术与公共议题相关；
4. 简短、易记、易引用。

据此：
- 序生、序生智能体：原创、无旧义、与 AI Agent 时代直接相关，最高；
- 序生协议、序生体、元网：原创且可独立使用，次高；
- 观测创造实在：短语完整、可独立引用，但与量子「观测者效应」有混淆风险，居中；
- 元意识、元识、元知、元子：重要，但在心理学、佛学、古典哲学中已有用法，逃逸阻力大，靠后。
"""

CATEGORY_ORDER = ["序生体系", "本体论模型", "元意识体系", "元子社会"]

# 首页前几张卡片：按逃逸概率从高到低
FRONT_TERMS = [
    "序生",
    "序生智能体",
    "元网",
    "元意识",
    "观测创造实在",
    "元知",
    "元子",
]

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


def front_rank(term: str) -> int:
    try:
        return FRONT_TERMS.index(term)
    except ValueError:
        return len(FRONT_TERMS)


def ordered_categories(stats: dict) -> list[tuple[str, int]]:
    items = list(stats.items())
    return sorted(items, key=lambda kv: (category_rank(kv[0]), -kv[1]))
