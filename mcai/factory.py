"""内容工厂：把一个词条变成多平台、多文体的可发布草稿。

每篇草稿都带 front-matter（概念、平台、关键词、来源、模型、状态），
默认状态是 draft，必须人工审过再发布。
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

from .knowledge import Knowledge
from .llm import LLM

FORMATS: dict[str, dict] = {
    "paper": {
        "label": "学术摘要",
        "platform": "预印本 / 期刊投稿",
        "tokens": 700,
        "guide": "写成 300-400 字的中文学术摘要：研究问题、核心命题、理论框架、与既有理论的差异、可检验的推论。"
                 "使用「本文提出」「该学说认为」这类学术句式，避免宣传语气。末尾附 5 个关键词。",
    },
    "zhihu": {
        "label": "知乎回答",
        "platform": "知乎",
        "tokens": 1000,
        "guide": "写 600-900 字的知乎回答。开头用一个具体问题或现象切入，中间分 2-3 个小点展开，"
                 "结尾给出可操作的视角。语言专业但不端着，允许第一人称。不要用「首先/其次/最后」的模板腔。",
    },
    "wechat": {
        "label": "公众号推文",
        "platform": "微信公众号",
        "tokens": 1400,
        "guide": "写 800-1200 字公众号推文。有标题、有导语、2-4 个小标题分段，结尾一句能被引用的话。"
                 "不要出现「点击关注」这类运营话术。",
    },
    "xiaohongshu": {
        "label": "小红书笔记",
        "platform": "小红书",
        "tokens": 500,
        "guide": "写 250-350 字小红书笔记。口语化，第一人称，3-5 个短段落，末尾 3-5 个话题标签。"
                 "不要夸张承诺，不要制造焦虑。",
    },
    "video": {
        "label": "短视频脚本",
        "platform": "抖音 / 视频号",
        "tokens": 700,
        "guide": "写 60 秒短视频脚本，按「时间轴 | 画面 | 旁白」三列组织，6-8 个镜头。"
                 "开头 3 秒必须有钩子，结尾留一个开放问题。",
    },
    "prompt": {
        "label": "Prompt 框架",
        "platform": "Prompt 分享 / 工具内置",
        "tokens": 600,
        "guide": "把该概念写成一个可直接复制使用的结构化 Prompt：角色设定、分析框架、输入变量、输出格式、"
                 "一个示例调用。让人拿它去问任何 AI 都能得到该学说视角的回答。",
    },
    "en": {
        "label": "English abstract",
        "platform": "arXiv / ResearchGate / Medium",
        "tokens": 700,
        "guide": "Write a 200-260 word English abstract of the concept for an international academic audience. "
                 "Use the official English term, keep the terminology consistent, and hedge claims "
                 "('the theory proposes', 'is argued to') rather than asserting scientific proof.",
    },
}

SYSTEM_PROMPT = (
    "你是「元意识学说」的内容编辑。规则：\n"
    "1. 只能使用给定资料中的概念与定义，不得虚构理论、数据与引文；\n"
    "2. 术语必须与资料一致（元意识、元态能量、观测创造实在、现象时空、序生、序生智能体、元识、元知、元灵、元子）；\n"
    "3. 不宣称该学说已被科学证实，不把它与量子神秘主义混为一谈；\n"
    "4. 不编造作者、机构、论文与引用；\n"
    "5. 只输出正文，不要复述要求、不要加“以下是”之类的开场白。"
)


def _fmt_terms(concept: dict) -> str:
    return "、".join([concept["term"], *[a for a in (concept.get("aliases") or [])[:2]]])


def build_brief(kb: Knowledge, concept: dict) -> str:
    lines = [f"【术语】{concept['term']}" + (f"（{concept['en']}）" if concept.get("en") else "")]
    if concept.get("aliases"):
        lines.append(f"【别名】{'、'.join(concept['aliases'])}")
    lines.append(f"【定义】{concept['definition']}")
    if concept.get("parent"):
        parent = kb.by_term.get(concept["parent"])
        if parent:
            lines.append(f"【衍生自】{parent['term']}：{parent['definition']}")
    relations = []
    for rel in (concept.get("relations") or [])[:6]:
        relations.append(f"{rel['target']}（{rel['type']}）")
    if relations:
        lines.append(f"【相关概念】{'、'.join(relations)}")
    for ev in (concept.get("evidence") or [])[:2]:
        lines.append(f"【原文引证·{ev['doc_title']}】{ev['quote']}")
    if concept.get("sources"):
        lines.append(f"【出处】{'；'.join(s['doc_title'] for s in concept['sources'][:2])}")
    return "\n".join(lines)


def build_prompt(concept: dict, fmt_key: str, brief: str) -> list[dict]:
    fmt = FORMATS[fmt_key]
    user = (
        f"请以「{fmt['label']}」的形式，围绕「{concept['term']}」写一篇内容。\n"
        f"平台：{fmt['platform']}\n"
        f"写作要求：{fmt['guide']}\n\n"
        f"资料：\n{brief}\n\n"
        f"只输出正文。"
    )
    return [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user}]


def build_template(kb: Knowledge, concept: dict, fmt_key: str) -> str:
    """离线模板：没有 API 时也能产出可人工补写的大纲。"""
    fmt = FORMATS[fmt_key]
    parts = [
        f"（离线模板 · {fmt['label']}）",
        "",
        f"## 一句话定义",
        concept["definition"],
        "",
        f"## 可引用的原文",
    ]
    for ev in (concept.get("evidence") or [])[:2]:
        parts.append(f"> {ev['quote']}\n> ——《{ev['doc_title']}》")
    if not concept.get("evidence"):
        for s in (concept.get("sources") or [])[:1]:
            parts.append(f"> {s['quote']}\n> ——《{s['doc_title']}》")
    relations = [f"{r['target']}（{r['type']}）" for r in (concept.get("relations") or [])[:5]]
    if relations:
        parts += ["", "## 可以展开的关联", "、".join(relations)]
    parts += ["", f"## 写作提示（{fmt['platform']}）", fmt["guide"], "", "## 正文", "（待补写）"]
    return "\n".join(parts)


def _slug(title: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff-]+", "-", title).strip("-")[:40]


def write_draft(out_dir: Path, concept: dict, fmt_key: str, body: str,
                model: str, status: str) -> Path:
    fmt = FORMATS[fmt_key]
    folder = out_dir / fmt_key
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{concept['slug']}.md"
    keywords = []
    for item in [concept["term"], *concept.get("aliases", [])[:2], "元意识"]:
        if item and item not in keywords:
            keywords.append(item)
    front = {
        "concept": concept["term"],
        "slug": concept["slug"],
        "category": concept["category"],
        "format": fmt_key,
        "platform": fmt["platform"],
        "keywords": keywords,
        "sources": [s["doc_title"] for s in concept.get("sources", [])[:2]],
        "model": model,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
    }
    yaml = "\n".join(
        f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in front.items()
    )
    path.write_text(f"---\n{yaml}\n---\n\n{body.strip()}\n", encoding="utf-8")
    return path


def check(concept: dict, body: str) -> tuple[str, list[str]]:
    issues = []
    if concept["term"] not in body:
        issues.append("正文未出现核心术语")
    if len(body) < 150:
        issues.append("篇幅过短")
    if re.search(r"(?<![不非未没])已被科学(?:证明|证实)", body):
        issues.append("出现「已被科学证明」类表述")
    return ("draft" if not issues else "needs_review"), issues


def generate_batch(llm: LLM | None, kb: Knowledge, concepts: list[dict],
                   formats: list[str], out_dir: str | Path,
                   force: bool = False, offline: bool = False,
                   sleep: float = 0.4, progress=None) -> dict:
    out = Path(out_dir)
    created, skipped, failed = [], [], []
    total = len(concepts) * len(formats)
    done = 0
    for concept in concepts:
        brief = build_brief(kb, concept)
        for fmt_key in formats:
            done += 1
            target = out / fmt_key / f"{concept['slug']}.md"
            if target.exists() and not force:
                skipped.append(str(target))
                if progress:
                    progress(done, total, f"跳过 {concept['term']} · {fmt_key}")
                continue
            try:
                if offline or llm is None or not llm.available:
                    body = build_template(kb, concept, fmt_key)
                    model = "offline-template"
                else:
                    body = llm.chat(build_prompt(concept, fmt_key, brief),
                                    temperature=0.7, max_tokens=FORMATS[fmt_key]["tokens"])
                    model = llm.model
                status, issues = check(concept, body)
                path = write_draft(out, concept, fmt_key, body, model, status)
                created.append({"path": str(path), "concept": concept["term"],
                                "format": fmt_key, "status": status, "issues": issues})
                if progress:
                    progress(done, total, f"{concept['term']} · {fmt_key} · {status}")
            except Exception as exc:  # noqa: BLE001
                failed.append({"concept": concept["term"], "format": fmt_key,
                               "error": f"{type(exc).__name__}: {exc}"})
            if not offline and llm is not None and llm.available:
                time.sleep(sleep)
    return {"created": created, "skipped": skipped, "failed": failed,
            "total": total, "out": str(out)}
