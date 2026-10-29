"""语料装载：把 docx / pdf / txt 统一成带章节路径的段落块。"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from . import pdftext
from .text import clean

TERM_LINE = re.compile(
    r"^\s*([^\s：:，。；、！？()（）《》\"']{2,16})\s*(?:[：:]|——|—|＝|=)\s*(.{8,})$"
)
_HEADING_STYLE = re.compile(r"^(Heading|标题)\s*(\d)?", re.I)
_HEADING_NOISE = re.compile(r"[。！？；，,;]$")


@dataclass
class Block:
    doc_id: str
    doc_title: str
    order: int
    text: str
    style: str = "Normal"
    section: tuple[str, ...] = ()
    location: str = ""

    @property
    def is_term_line(self) -> bool:
        return bool(TERM_LINE.match(self.text))


@dataclass
class Document:
    doc_id: str
    title: str
    path: str
    kind: str
    priority: int
    blocks: list[Block] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(b.text for b in self.blocks)

    def sections(self) -> list[str]:
        seen: list[str] = []
        for b in self.blocks:
            for s in b.section:
                if s not in seen:
                    seen.append(s)
        return seen


@dataclass
class Corpus:
    project: dict
    keywords: list[str]
    term_blacklist: list[str]
    slugs: dict[str, str]
    documents: list[Document]

    @property
    def blocks(self) -> Iterable[Block]:
        for doc in self.documents:
            yield from doc.blocks

    def find(self, doc_id: str) -> Document | None:
        return next((d for d in self.documents if d.doc_id == doc_id), None)


def load_config(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _docx_blocks(doc: Document, path: Path) -> list[Block]:
    from docx import Document as Docx
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    parsed = Docx(str(path))
    blocks: list[Block] = []
    section: list[str] = []
    order = 0

    def push(text: str, style: str, location: str) -> None:
        nonlocal order
        # Word 常把多条定义用「手动换行符」塞进同一段落，这里按换行拆开
        for part in re.split(r"[\r\n\u000b\u2028\u2029]", text or ""):
            part = clean(part)
            if not part:
                continue
            m = _HEADING_STYLE.match(style or "")
            if m and style != "Table":
                level = int(m.group(2) or 1)
                del section[level - 1:]
                section.append(part)
            blocks.append(
                Block(doc.doc_id, doc.title, order, part, style or "Normal", tuple(section), location)
            )
            order += 1

    body = parsed.element.body
    for child in body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            para = Paragraph(child, parsed)
            push(para.text, para.style.name if para.style is not None else "Normal", f"p{order + 1}")
        elif tag == "tbl":
            table = Table(child, parsed)
            for row in table.rows:
                cells = [clean(c.text.replace("\n", " ")) for c in row.cells]
                push(" | ".join(c for c in cells if c), "Table", f"t{order + 1}")

    _promote_section_titles(blocks)
    return blocks


def _promote_section_titles(blocks: list[Block]) -> None:
    """把「元意识体系」这类无样式短标题提升为章节。

    判定：Normal 样式、长度 2-20、无句末标点，且后续三个块内出现「术语：定义」。
    两遍处理：先定位标题，再按最近标题归属，避免后一个标题被前一个吞掉。
    """
    titles: dict[int, str] = {}
    for i, block in enumerate(blocks):
        if block.style not in ("Normal", "Normal (Web)"):
            continue
        text = block.text
        if not (2 <= len(text) <= 20) or _HEADING_NOISE.search(text) or text.endswith("："):
            continue
        sep = re.search(r"[：:=]|——|—", text)
        if sep and len(text[: sep.start()].strip()) < 4:
            continue
        if TERM_LINE.match(text) or text in ("结论表述", "结论"):
            continue
        if any(b.is_term_line for b in blocks[i + 1: i + 4]):
            titles[i] = text

    current: str | None = None
    for i, block in enumerate(blocks):
        if i in titles:
            current = titles[i]
        if current and len(block.section) <= 1:
            block.section = (block.doc_title, current)


def _pdf_blocks(doc: Document, path: Path) -> list[Block]:
    blocks: list[Block] = []
    for page_no, page in enumerate(pdftext.extract_pdf_text(str(path)), 1):
        for line_no, line in enumerate(page.split("\n")):
            text = clean(line)
            if text:
                blocks.append(
                    Block(doc.doc_id, doc.title, len(blocks), text, "PDF", (), f"p{page_no}:{line_no + 1}")
                )
    return blocks


def _text_blocks(doc: Document, path: Path, style: str) -> list[Block]:
    blocks: list[Block] = []
    section: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        text = clean(raw)
        if not text:
            continue
        if text.startswith("#"):
            level = len(text) - len(text.lstrip("#"))
            title = text.lstrip("#").strip()
            del section[level - 1:]
            section.append(title)
            blocks.append(Block(doc.doc_id, doc.title, len(blocks), title, style, tuple(section), ""))
        else:
            blocks.append(Block(doc.doc_id, doc.title, len(blocks), text, style, tuple(section), ""))
    return blocks


def _resolve_path(path: Path) -> Path:
    """文件被改名（如加了「3、」前缀）时，按文件名后缀就近找回，避免配置失效。"""
    if path.exists():
        return path
    candidates = sorted(p for p in path.parent.glob(f"*{path.suffix}") if p.name.endswith(path.name))
    return candidates[0] if candidates else path


def load_document(spec: dict, base: Path | None = None) -> Document:
    raw = Path(spec["path"]).expanduser()
    if not raw.is_absolute() and base is not None:
        raw = base / raw
    path = _resolve_path(raw)
    doc = Document(
        doc_id=spec["id"],
        title=spec.get("title") or path.stem,
        path=str(path),
        kind=spec.get("kind", "other"),
        priority=int(spec.get("priority", 50)),
    )
    if not path.exists():
        raise FileNotFoundError(f"语料缺失：{path}")
    suffix = path.suffix.lower()
    if suffix == ".docx":
        doc.blocks = _docx_blocks(doc, path)
    elif suffix == ".pdf":
        doc.blocks = _pdf_blocks(doc, path)
    elif suffix in (".txt", ".md"):
        doc.blocks = _text_blocks(doc, path, "Text")
    else:
        raise ValueError(f"暂不支持的文件类型：{suffix}")
    return doc


def load_corpus(config_path: str | Path) -> Corpus:
    cfg = load_config(config_path)
    base = Path(config_path).resolve().parent.parent
    docs = [load_document(spec, base) for spec in cfg["corpus"]]
    return Corpus(
        project=cfg["project"],
        keywords=cfg.get("keywords", []),
        term_blacklist=cfg.get("term_blacklist", []),
        slugs=cfg.get("slugs", {}),
        documents=docs,
    )
