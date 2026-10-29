"""文本规范化与相似度工具（纯标准库）。"""
from __future__ import annotations

import difflib
import re

_WS = re.compile(r"[\s\u3000\u00a0]+")
_QUOTES = str.maketrans({"\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'"})
_SENT = re.compile(r"(?<=[。！？!?；;])\s*")
_PUNCT = re.compile(r"[，。、；：！？\u201c\u201d\u2018\u2019（）()《》〈〉【】\[\]·—…\-]")


def clean(text: str) -> str:
    """压缩空白，保留原始标点（用于展示）。"""
    return _WS.sub(" ", text or "").strip()


def normalize(text: str) -> str:
    """用于比较的归一化：去空白、统一引号、去常见标点。"""
    return _PUNCT.sub("", clean(text).translate(_QUOTES)).lower()


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT.split(clean(text)) if s.strip()]


def first_sentence(text: str, limit: int = 120) -> str:
    for s in sentences(text):
        if len(s) >= 8:
            return s if len(s) <= limit else s[:limit].rstrip("，,、") + "……"
    return clean(text)[:limit]


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    # autojunk 会把中文高频字当成噪声，长文本相似度会严重失真
    return difflib.SequenceMatcher(None, normalize(a), normalize(b), autojunk=False).ratio()


def coverage(shorter: str, longer: str, n: int = 4) -> float:
    """短文本的 n-gram 有多大比例被长文本覆盖，用于识别「截断版」而非「冲突版」。"""
    s, l = normalize(shorter), normalize(longer)
    if len(s) < n or len(l) < n:
        return 0.0
    grams = {s[i: i + n] for i in range(len(s) - n + 1)}
    if not grams:
        return 0.0
    hit = sum(1 for g in grams if g in l)
    return hit / len(grams)


def contains_term(text: str, term: str) -> bool:
    """术语是否作为独立片段出现在文本中（避免“元意识”命中“个体元意识”误判不算问题）。"""
    return term in text


def md5_short(text: str, n: int = 8) -> str:
    import hashlib

    return hashlib.md5(text.encode("utf-8")).hexdigest()[:n]
