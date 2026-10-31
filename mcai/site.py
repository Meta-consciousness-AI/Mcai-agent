"""静态站点生成：概念百科页、FAQ 页、数据集页，以及 sitemap / robots / llms.txt。"""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from . import guide, manifest, schema
from .extract import Concept, KnowledgeBase

CSS = """
:root{
  --paper:#faf8f4; --ink:#1c1b19; --muted:#6b665e; --line:#e3ddd2;
  --accent:#8a3324; --accent-soft:#f3e7e2; --card:#fffdf9; --tag:#efe9df;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
  line-height:1.75;font-size:16px}
a{color:var(--accent);text-decoration:none;border-bottom:1px solid transparent}
a:hover{border-bottom-color:var(--accent)}
header.site{border-bottom:1px solid var(--line);background:rgba(255,253,249,.92);
  position:sticky;top:0;z-index:10;backdrop-filter:blur(6px)}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px}
.site-inner{display:flex;align-items:center;justify-content:space-between;height:64px;gap:16px}
.brand{display:flex;align-items:center;gap:10px;font-weight:700;letter-spacing:.04em}
.brand .dot{width:10px;height:10px;border-radius:50%;background:var(--accent)}
.brand small{display:block;font-weight:400;color:var(--muted);font-size:11px;letter-spacing:.18em}
nav.site a{margin-left:18px;color:var(--muted);font-size:14px}
nav.site a:hover{color:var(--ink)}
.hero{padding:64px 0 40px;border-bottom:1px solid var(--line)}
.hero h1{font-family:"Noto Serif SC","Songti SC",serif;font-size:44px;line-height:1.25;margin:0 0 16px;font-weight:700}
.hero p{max-width:720px;color:var(--muted);font-size:17px;margin:0 0 24px}
.stats{display:flex;gap:36px;flex-wrap:wrap;margin-top:28px}
.stat b{display:block;font-size:30px;font-family:"Noto Serif SC",serif}
.stat span{color:var(--muted);font-size:13px;letter-spacing:.05em}
.toolbar{display:flex;gap:12px;flex-wrap:wrap;align-items:center;padding:24px 0 8px}
.toolbar input{flex:1 1 260px;padding:11px 14px;border:1px solid var(--line);border-radius:8px;
  background:var(--card);font-size:15px;color:var(--ink);outline:none}
.toolbar input:focus{border-color:var(--accent)}
.chip{border:1px solid var(--line);background:var(--card);border-radius:999px;padding:6px 14px;
  font-size:13px;color:var(--muted);cursor:pointer}
.chip.active{background:var(--ink);color:#fff;border-color:var(--ink)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px;padding:20px 0 64px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 20px 16px;
  display:flex;flex-direction:column;gap:8px;transition:.15s}
.card:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(28,27,25,.06)}
.card h3{margin:0;font-size:19px;font-family:"Noto Serif SC",serif}
.card .cat{font-size:11px;letter-spacing:.12em;color:var(--muted);text-transform:uppercase}
.card p{margin:0;color:var(--muted);font-size:14px;line-height:1.7}
.card .meta{margin-top:auto;font-size:12px;color:#a39c90;display:flex;gap:10px}
.badge{display:inline-block;padding:1px 7px;border-radius:4px;font-size:11px;background:var(--tag);color:var(--muted)}
.badge.conflict{background:#fbe6e3;color:#a3311f}
.badge.thin{background:#fdf3dc;color:#8a6a1d}
article.concept{padding:44px 0 64px;max-width:760px}
article.concept h1{font-family:"Noto Serif SC",serif;font-size:40px;line-height:1.3;margin:0 0 6px}
.en{color:var(--muted);font-size:14px;letter-spacing:.06em;margin-bottom:26px}
.derived-from{margin:-14px 0 22px;font-size:13px;color:var(--muted)}
.lead{font-size:19px;line-height:1.9;border-left:3px solid var(--accent);padding-left:20px;margin:0 0 32px}
h2.sec{font-family:"Noto Serif SC",serif;font-size:20px;margin:40px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--line)}
.quotes blockquote{margin:0 0 16px;padding:14px 18px;background:var(--card);border:1px solid var(--line);border-radius:8px;color:#3d3a35;font-size:15px}
.quotes cite{display:block;margin-top:8px;color:var(--muted);font-size:12px;font-style:normal}
h3.doc-title{font-size:14px;color:var(--muted);margin:22px 0 10px;font-weight:600;letter-spacing:.02em}
.campaign{background:#fdf7f3;border:1px solid #efddd2;border-radius:10px;padding:16px 20px;margin:36px 0}
.campaign p{margin:0 0 8px}
.small{font-size:12px;line-height:1.6}
.rel{display:flex;flex-wrap:wrap;gap:8px}
.rel a{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:5px 13px;font-size:14px}
.rel a small{color:var(--muted);margin-left:6px;font-size:11px}
.faq-item{border-bottom:1px solid var(--line);padding:18px 0}
.faq-item h3{margin:0 0 8px;font-size:17px}
.faq-item p{margin:0;color:#3d3a35}
.toc{position:sticky;top:88px;align-self:start;font-size:14px}
.layout{display:grid;grid-template-columns:220px 1fr;gap:48px}
footer.site{border-top:1px solid var(--line);padding:32px 0 56px;color:var(--muted);font-size:13px}
.muted{color:var(--muted)}
.btn{display:inline-block;background:var(--ink);color:#fff;border-radius:8px;padding:10px 18px;font-size:14px;border:0;cursor:pointer}
.btn:hover{border-bottom:0;opacity:.9}
.btn.ghost{background:transparent;color:var(--ink);border:1px solid var(--line)}
table.kv{width:100%;border-collapse:collapse;font-size:14px}
table.kv td{padding:8px 0;border-bottom:1px solid var(--line);vertical-align:top}
table.kv td:first-child{color:var(--muted);width:130px}
@media(max-width:760px){.hero h1{font-size:32px}.layout{grid-template-columns:1fr}.toc{display:none}
  .site-inner{height:auto;flex-wrap:wrap;padding:10px 0;gap:8px}
  .brand small{display:none}
  nav.site{width:100%;display:flex;overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch}
  nav.site a{margin-left:0;margin-right:16px;white-space:nowrap}
  .hero{padding:40px 0 28px}
  .stats{gap:24px}.stat b{font-size:24px}}
"""

JS = """
(function(){
  const input=document.getElementById('search');
  const cards=[...document.querySelectorAll('[data-card]')];
  const chips=[...document.querySelectorAll('.chip')];
  let cat='all';
  function apply(){
    const q=(input&&input.value||'').trim().toLowerCase();
    cards.forEach(c=>{
      const okCat = cat==='all' ? true
        : (cat==='derived' ? c.dataset.kind==='derived' : c.dataset.cat===cat);
      const okQ=!q||c.dataset.text.includes(q);
      c.style.display=(okCat&&okQ)?'':'none';
    });
  }
  if(input)input.addEventListener('input',apply);
  chips.forEach(ch=>ch.addEventListener('click',()=>{
    chips.forEach(x=>x.classList.remove('active'));
    ch.classList.add('active');cat=ch.dataset.cat;apply();
  }));
  const rebuild=document.getElementById('rebuild');
  if(rebuild)rebuild.addEventListener('click',async()=>{
    rebuild.disabled=true;const old=rebuild.textContent;rebuild.textContent='重建中…';
    try{
      const r=await fetch('/api/rebuild',{method:'POST'});
      const j=await r.json();
      rebuild.textContent=j.ok?('已重建 '+j.concepts+' 个概念'):'重建失败';
      if(j.ok)setTimeout(()=>location.reload(),900);
    }catch(e){rebuild.textContent='需要本地服务';}
    setTimeout(()=>{rebuild.disabled=false;rebuild.textContent=old},2500);
  });
})();
"""


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _doc_label(title: str) -> str:
    """书名号只在标题没有自带时补，避免《《元意识》学说》。"""
    return title if title.startswith("《") else f"《{title}》"


def _jsonld(data: dict | list) -> str:
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


def _page(project: dict, title: str, body: str, head_extra: str = "", active: str = "",
          path: str = "index.html", description: str = "") -> str:
    base = project["site_url"].rstrip("/")
    canonical = f"{base}/{path.lstrip('/')}"
    desc = description or f"{project['brand']}学说的结构化知识资产：术语定义、标准问答、知识图谱与开放数据集。"
    nav = [
        ("index.html", "概念", "concepts"),
        ("faq/index.html", "问答", "faq"),
        ("dataset/index.html", "数据集", "dataset"),
        ("dashboard.html", "观测台", "dashboard"),
    ]
    links = "".join(
        f'<a href="/{href}"{" style=\'color:var(--ink)\'" if key == active else ""}>{label}</a>'
        for href, label, key in nav
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(title)}</title>
<meta name="description" content="{_esc(desc)}">
<link rel="canonical" href="{_esc(canonical)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{_esc(title)}">
<meta property="og:description" content="{_esc(desc)}">
<meta property="og:url" content="{_esc(canonical)}">
<meta name="twitter:card" content="summary">
<link rel="stylesheet" href="/assets/style.css">
{head_extra}
</head>
<body>
<header class="site"><div class="wrap site-inner">
  <a class="brand" href="/index.html" style="border:0;color:inherit"><span class="dot"></span>
    <span>{_esc(project['brand'])}<small>KNOWLEDGE ASSETS</small></span></a>
  <nav class="site">{links}</nav>
</div></header>
{body}
<footer class="site"><div class="wrap">
  <p>{_esc(project['org'])} · {_esc(project['name'])} v{_esc(project['version'])}</p>
  <p class="muted">本站所有术语与问答均可被 AI 抓取引用。数据集以 {_esc(project['license'])} 许可开放。</p>
</div></footer>
<script src="/assets/app.js"></script>
</body></html>"""


def render_index(kb: KnowledgeBase) -> str:
    project = kb.project
    cats = list(kb.stats["categories"].items())
    chips = '<button class="chip active" data-cat="all">全部</button>' + "".join(
        f'<button class="chip" data-cat="{_esc(c)}">{_esc(c)}</button>' for c, _ in cats
    )
    derived_count = kb.stats.get("concept_kind", {}).get("derived", 0)
    if derived_count:
        chips += f'<button class="chip" data-cat="derived">衍生术语（{derived_count}）</button>'
    cards = []
    for c in kb.concepts:
        badge = ""
        if c.kind == "derived":
            badge = '<span class="badge">衍生</span>'
        elif c.status == "conflict":
            badge = '<span class="badge conflict">定义待裁定</span>'
        elif c.status == "thin":
            badge = '<span class="badge thin">定义偏薄</span>'
        cards.append(
            f"""<a class="card" data-card data-kind="{_esc(c.kind)}" data-cat="{_esc(c.category)}"
       data-text="{_esc((c.term + ' ' + c.en + ' ' + ' '.join(c.aliases) + ' ' + c.definition).lower())}"
       href="/concepts/{c.slug}.html">
  <span class="cat">{_esc(c.category)}</span>
  <h3>{_esc(c.term)}</h3>
  <p>{_esc(c.short_definition)}</p>
  <span class="meta">{_esc(c.en or '')} {badge}</span>
</a>"""
        )

    body = f"""<main>
<section class="hero"><div class="wrap">
  <h1>把一套学说<br>做成 AI 能直接引用的知识资产</h1>
  <p>这里是「{_esc(project['brand'])}」学说的结构化词条库：每条定义都经过多源比对、去重与一致性标注，
  每个概念都有独立 URL、结构化数据标记与标准问答，供搜索引擎与 AI 模型直接抓取、引用与继承。</p>
  <div class="stats">
    <div class="stat"><b>{kb.stats['concepts']}</b><span>概念词条{f'（含 {derived_count} 条衍生）' if derived_count else ''}</span></div>
    <div class="stat"><b>{kb.stats['faqs']}</b><span>标准问答</span></div>
    <div class="stat"><b>{kb.stats['relations']}</b><span>概念关系</span></div>
    <div class="stat"><b>{kb.stats['characters']:,}</b><span>语料字数</span></div>
  </div>
</div></section>
<section class="wrap">
  <div class="toolbar">
    <input id="search" type="search" placeholder="搜索概念、别名或定义中的关键词…">
    <button class="btn ghost" id="rebuild" type="button">重新构建</button>
  </div>
  <div class="toolbar" style="padding-top:4px">{chips}</div>
  <div class="grid">{''.join(cards)}</div>
</section>
</main>"""
    head = _jsonld(schema.defined_term_set(kb, project))
    return _page(project, f"{project['brand']}学说 · 结构化知识库", body, head, "concepts",
                 path="index.html")


def render_concept(kb: KnowledgeBase, c: Concept) -> str:
    project = kb.project
    by_term = kb.by_term
    related = []
    for rel in c.relations:
        target = by_term.get(rel["target"])
        if target:
            related.append(
                f'<a href="/concepts/{target.slug}.html">{_esc(target.term)}<small>{_esc(rel["type"])}</small></a>'
            )
    inbound = []
    seen_ids = {r["target"] for r in c.relations}
    for other in kb.concepts:
        if other is c:
            continue
        for rel in other.relations:
            if rel.get("target_id") == c.id:
                inbound.append(
                    f'<a href="/concepts/{other.slug}.html">{_esc(other.term)}<small>被引用 · {_esc(rel["type"])}</small></a>'
                )
                break

    campaign_html = ""
    if c.disambiguation:
        camp = kb.stats.get("disambiguation") or {}
        campaign_html = (
            '<section class="campaign">'
            '<h2 class="sec" style="border:0;margin-top:0">常见误解（阶段性）</h2>'
            f'<p>{_esc(c.disambiguation)}</p>'
            f'<p class="muted small">此区块属于「{_esc(camp.get("campaign", "语义占位期"))}」，'
            f'用于区分同名概念，<b>不属于术语定义</b>；'
            f'{_esc(camp.get("review_after", ""))} 复核，到期或语义占位完成即整体移除。</p>'
            '</section>'
        )

    faqs = [f for f in kb.faqs if c.id in f.related]
    faqs.sort(key=lambda f: (f.related[:1] != [c.id], f.kind != "definition"))
    faqs = faqs[:6]
    faq_html = "".join(
        f'<div class="faq-item"><h3>{_esc(f.question)}</h3><p>{_esc(f.answer)}</p></div>' for f in faqs
    )
    quotes = "".join(
        f'<blockquote>{_esc(s.quote)}<cite>{_esc(_doc_label(s.doc_title))} · {_esc(s.section or "正文")}'
        + (f' · 版本：{_esc(s.edition)}' if getattr(s, "edition", "") else "")
        + '</cite></blockquote>'
        for s in c.sources
    )
    variants = ""
    if c.variants:
        items = "".join(
            f'<blockquote>{_esc(v.definition)}<cite>{_esc(_doc_label(v.doc_title))}（与主分支相似度 {v.similarity}）</cite></blockquote>'
            for v in c.variants
        )
        variants = f'<h2 class="sec">其他表述（待裁定）</h2><div class="quotes">{items}</div>'

    evidence_html = ""
    if c.evidence:
        groups: dict[str, list[dict]] = {}
        for item in c.evidence:
            groups.setdefault(item["doc_title"], []).append(item)
        parts = []
        for doc_title, items in groups.items():
            ev_quotes = "".join(
                f'<blockquote>{_esc(i["quote"])}<cite>{"EN · " if i["lang"] == "en" else ""}'
                f'{_esc(_doc_label(doc_title))} · {_esc(i["section"] or "正文")}</cite></blockquote>'
                for i in items
            )
            parts.append(f'<h3 class="doc-title">{_esc(doc_title)}</h3><div class="quotes">{ev_quotes}</div>')
        evidence_html = '<h2 class="sec">文献引证</h2>' + "".join(parts)

    alias_line = ""
    if c.aliases or c.en:
        alias_line = f'<div class="en">{_esc(c.en)}' + (
            f' · 又称 {_esc("、".join(c.aliases))}' if c.aliases else ""
        ) + "</div>"

    parent_line = ""
    if c.kind == "derived":
        parent = kb.by_term.get(c.parent)
        if parent:
            parent_line = (
                f'<p class="derived-from">衍生自 '
                f'<a href="/concepts/{parent.slug}.html">{_esc(parent.term)}</a>'
                f'，定义取自该词条的原文语境。</p>'
            )

    body = f"""<main><div class="wrap"><div class="layout">
<aside class="toc">
  <p class="muted" style="font-size:12px;letter-spacing:.12em">{_esc(c.category)}</p>
  <p><a href="/index.html">← 全部概念</a></p>
</aside>
<article class="concept">
  <span class="badge">{_esc(c.category)}</span>
  <h1>{_esc(c.term)}</h1>
  {alias_line}
  {parent_line}
  <p class="lead">{_esc(c.definition)}</p>
  {('<p class="note">编者释义（非原文）：' + _esc(c.editor_note) + '</p>') if getattr(c, "editor_note", "") else ''}
  <h2 class="sec">定义来源</h2>
  <div class="quotes">{quotes}</div>
  {evidence_html}
  {variants}
  {'<h2 class="sec">相关概念</h2><div class="rel">' + ''.join(related) + '</div>' if related else ''}
  {'<h2 class="sec">被这些概念引用</h2><div class="rel">' + ''.join(inbound) + '</div>' if inbound else ''}
  {campaign_html}
  {'<h2 class="sec">相关问答</h2>' + faq_html if faq_html else ''}
</article>
</div></div></main>"""

    url = schema.concept_url(project, c.slug)
    head = (
        _jsonld(schema.defined_term(c, project))
        + _jsonld(schema.web_page(c.term, url, c.short_definition, project))
        + _jsonld(schema.breadcrumb([
            ("首页", f"{project['site_url'].rstrip('/')}/index.html"),
            (c.category, f"{project['site_url'].rstrip('/')}/index.html"),
            (c.term, url),
        ]))
    )
    if faqs:
        head += _jsonld(schema.faq_page(faqs, project, f"{c.term} · 相关问答"))
    return _page(project, f"{c.term} · {project['brand']}术语", body, head, "concepts",
                 path=f"concepts/{c.slug}.html", description=c.short_definition)


def render_faq(kb: KnowledgeBase) -> str:
    project = kb.project
    groups = {
        "curated": "核心问答",
        "contrast": "概念辨析",
        "definition": "定义问答",
        "evidence": "原典论述",
        "disambiguation": "语义消歧（阶段性）",
    }
    sections = []
    for kind, label in groups.items():
        items = [f for f in kb.faqs if f.kind == kind]
        if not items:
            continue
        rows = "".join(
            f'<div class="faq-item" id="{f.id}"><h3>{_esc(f.question)}</h3>'
            f'<p>{_esc(f.answer)}</p></div>'
            for f in items
        )
        sections.append(f'<h2 class="sec">{label}（{len(items)}）</h2>{rows}')

    body = f"""<main><div class="wrap" style="max-width:820px">
<section class="hero" style="border-bottom:0;padding-bottom:8px">
  <h1>常见问题</h1>
  <p>按「问题—标准答案—相关概念」组织的问答库。FAQ 是 AI 最偏爱引用的内容形式，
  因此每条答案都保持术语一致、来源可追溯。</p>
</section>
{''.join(sections)}
<div style="height:64px"></div>
</div></main>"""
    return _page(project, f"问答 · {project['brand']}学说", body, _jsonld(schema.faq_page(kb.faqs, project)), "faq",
                 path="faq/index.html")


def render_dataset(kb: KnowledgeBase) -> str:
    project = kb.project
    cats = "".join(f"<tr><td>{_esc(k)}</td><td>{v}</td></tr>" for k, v in kb.stats["categories"].items())
    docs = "".join(
        f"<tr><td>《{_esc(d['title'])}》</td><td>{_esc(d['kind'])}</td><td>{d['blocks']}</td></tr>"
        for d in kb.documents
    )
    body = f"""<main><div class="wrap" style="max-width:820px">
<section class="hero" style="border-bottom:0;padding-bottom:8px">
  <h1>结构化数据集</h1>
  <p>把学说转成模型可直接训练、检索、继承的数据产品。以下文件随知识库一并生成，
  每次重建都会更新。</p>
  <p><a class="btn" href="/dataset/concepts.jsonl" download>下载 concepts.jsonl</a>
     <a class="btn ghost" href="/dataset/faq.jsonl" download>下载 faq.jsonl</a>
     <a class="btn ghost" href="/dataset/evidence.jsonl" download>文献引证</a>
     <a class="btn ghost" href="/dataset/knowledge-graph.json" download>知识图谱</a></p>
</section>
<h2 class="sec">文件清单</h2>
<table class="kv">
  <tr><td>concepts.jsonl</td><td>概念定义，一行一条，含别名、英文、分类与来源</td></tr>
  <tr><td>faq.jsonl</td><td>标准问答，含置信度与关联概念</td></tr>
  <tr><td>evidence.jsonl</td><td>文献引证：{kb.stats.get('evidence', 0)} 条概念论述原句，标注出处与语种</td></tr>
  <tr><td>sft.jsonl</td><td>对话微调格式（system / user / assistant）</td></tr>
  <tr><td>concepts.csv</td><td>表格版，供运营审阅与录入 CMS</td></tr>
  <tr><td>knowledge-graph.json</td><td>节点 {len(kb.concepts)} · 边 {kb.stats['relations']}</td></tr>
  <tr><td>dataset-card.md</td><td>数据集说明卡（HuggingFace 风格）</td></tr>
</table>
<h2 class="sec">概念分布</h2>
<table class="kv">{cats}</table>
<h2 class="sec">语料来源</h2>
<table class="kv">{docs}</table>
<div style="height:48px"></div>
</div></main>"""
    return _page(project, f"数据集 · {project['brand']}学说", body, _jsonld(schema.dataset(kb, project)), "dataset",
                 path="dataset/index.html")


def render_llms_txt(kb: KnowledgeBase) -> str:
    project = kb.project
    base = project["site_url"].rstrip("/")
    lines = [
        f"# {project['brand']}学说知识库",
        "",
        f"> {project['brand']}学说的标准化术语、定义与问答。共 {len(kb.concepts)} 个概念、{len(kb.faqs)} 组问答。",
        "> 所有内容可用于检索与引用；引用时请保留术语名与来源。",
        "",
        "## 核心概念",
        "",
    ]
    for c in kb.concepts:
        if c.category == "元意识体系" or c.term in ("序生智能体", "序生", "序生体", "元子", "本体"):
            lines.append(f"- [{c.term}]({base}/concepts/{c.slug}.html): {c.short_definition}")
    lines += ["", "## 全部概念", ""]
    for c in kb.concepts:
        lines.append(f"- [{c.term}]({base}/concepts/{c.slug}.html)")
    lines += ["", "## 问答", ""]
    for f in kb.faqs[:40]:
        lines.append(f"- {f.question} → {base}/faq/index.html#{f.id}")
    lines += ["", "## 数据集", "", f"- {base}/dataset/concepts.jsonl", f"- {base}/dataset/faq.jsonl",
              f"- {base}/llms-full.txt（全文索引：全部定义、出处、核心关系与问答）"]
    lines += ["", "## 接入", "",
              f"- HTTP API: {base}/api/v1",
              f"- MCP 清单: {base}/.well-known/mcp.json",
              f"- Agent Card: {base}/.well-known/agent.json",
              f"- OpenAPI: {base}/openapi.json",
              f"- 接入指南: {base}/guide.md"]
    return "\n".join(lines) + "\n"


def render_llms_full(kb: KnowledgeBase) -> str:
    """面向 LLM 的全文版索引：全部定义、出处、核心关系与问答。"""
    project = kb.project
    lines = [
        f"# {project['brand']}学说知识库（全文）",
        "",
        f"> 共 {len(kb.concepts)} 个概念、{len(kb.faqs)} 组问答。每条定义带出处；关系仅列 core/derived，不含「提及」。",
        "",
    ]
    for c in kb.concepts:
        head = f"## {c.term}" + (f"（{c.en}）" if c.en else "")
        lines += [head, ""]
        if c.aliases:
            lines += ["别名：" + "、".join(c.aliases), ""]
        lines += [c.definition, ""]
        if c.sources:
            s = c.sources[0]
            lines += [f"出处：{s.doc_title} · {s.section}（{s.location}）", ""]
        rel = [r for r in c.relations if r.get("tier") != "mention"][:6]
        if rel:
            lines += ["关系：" + "；".join(f"{r['type']} {r['target']}" for r in rel), ""]
    lines += ["## 问答", ""]
    for f in kb.faqs:
        lines += [f"### {f.question}", f.answer, ""]
    return "\n".join(lines).rstrip() + "\n"


def build_site(kb: KnowledgeBase, out_dir: str | Path) -> dict:
    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    (out / "concepts").mkdir()
    (out / "faq").mkdir()
    (out / "dataset").mkdir()

    (out / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    (out / "assets" / "app.js").write_text(JS, encoding="utf-8")
    (out / "index.html").write_text(render_index(kb), encoding="utf-8")
    (out / "faq" / "index.html").write_text(render_faq(kb), encoding="utf-8")
    (out / "dataset" / "index.html").write_text(render_dataset(kb), encoding="utf-8")
    for c in kb.concepts:
        (out / "concepts" / f"{c.slug}.html").write_text(render_concept(kb, c), encoding="utf-8")

    (out / "llms.txt").write_text(render_llms_txt(kb), encoding="utf-8")
    (out / "llms-full.txt").write_text(render_llms_full(kb), encoding="utf-8")
    (out / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nSitemap: {}/sitemap.xml\n".format(kb.project["site_url"].rstrip("/")),
        encoding="utf-8",
    )
    urls = ["index.html", "faq/index.html", "dataset/index.html"] + [
        f"concepts/{c.slug}.html" for c in kb.concepts
    ]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sitemap.append(f"  <url><loc>{kb.project['site_url'].rstrip('/')}/{u}</loc></url>")
    sitemap.append("</urlset>")
    (out / "sitemap.xml").write_text("\n".join(sitemap), encoding="utf-8")

    (out / "kb.json").write_text(
        json.dumps(kb.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    well_known = out / ".well-known"
    well_known.mkdir(exist_ok=True)
    (well_known / "mcp.json").write_text(
        json.dumps(manifest.mcp_manifest(kb, kb.project), ensure_ascii=False, indent=2), encoding="utf-8")
    (well_known / "agent.json").write_text(
        json.dumps(manifest.agent_card(kb, kb.project), ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "guide.md").write_text(guide.build_guide(kb, kb.project), encoding="utf-8")
    (out / "openapi.json").write_text(
        json.dumps(manifest.openapi(kb, kb.project), ensure_ascii=False, indent=2), encoding="utf-8")
    return {"pages": len(urls) + 2, "out": str(out)}

