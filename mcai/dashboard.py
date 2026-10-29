"""本地观测台：把自动巡检、调用统计、变更历史汇成一页静态 HTML。"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from .telemetry import Telemetry

CSS = """
body{margin:0;background:#faf8f4;color:#1c1b19;font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;line-height:1.7}
.wrap{max-width:1000px;margin:0 auto;padding:32px 24px 64px}
h1{font-family:"Noto Serif SC",serif;font-size:32px;margin:0 0 6px}
h2{font-family:"Noto Serif SC",serif;font-size:20px;margin:36px 0 12px;padding-bottom:8px;border-bottom:1px solid #e3ddd2}
.muted{color:#6b665e;font-size:13px}
.badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;background:#e8f3e8;color:#256b2f}
.badge.bad{background:#fbe6e3;color:#a3311f}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin-top:22px}
.card{background:#fffdf9;border:1px solid #e3ddd2;border-radius:12px;padding:16px}
.card b{display:block;font-size:26px;font-family:"Noto Serif SC",serif}
.card span{color:#6b665e;font-size:12px}
table{width:100%;border-collapse:collapse;font-size:14px;background:#fffdf9;border:1px solid #e3ddd2;border-radius:10px;overflow:hidden}
th,td{padding:9px 12px;border-bottom:1px solid #eee7db;text-align:left;vertical-align:top}
th{background:#f3eee4;font-weight:600;font-size:12px;color:#6b665e}
tr:last-child td{border-bottom:0}
.bars{display:flex;align-items:flex-end;gap:6px;height:90px;margin-top:12px}
.bar{flex:1;background:#c9b8a4;border-radius:3px 3px 0 0;min-height:2px}
.barlabel{font-size:10px;color:#6b665e;text-align:center}
.pill{display:inline-block;padding:1px 7px;border-radius:4px;background:#efe9df;font-size:11px;color:#6b665e;margin-right:4px}
a{color:#8a3324;text-decoration:none}
a:hover{text-decoration:underline}
.nav a{margin-right:16px}
.empty{color:#a39c90;font-size:13px;padding:8px 0}
"""


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _read_jsonl(path: Path, limit: int = 50) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows[-limit:]


def _bars(values: dict[str, int]) -> str:
    if not values or not any(values.values()):
        return '<div class="empty">暂无调用记录</div>'
    peak = max(values.values()) or 1
    out = ['<div class="bars">']
    for day, count in values.items():
        height = max(2, int(78 * count / peak))
        out.append(f'<div class="bar" style="height:{height}px" title="{day}: {count}"></div>')
    out.append("</div><div style=\"display:flex;gap:6px\">")
    for day in values:
        out.append(f'<div class="barlabel" style="flex:1">{day[5:]}</div>')
    out.append("</div>")
    return "".join(out)


def render(root: str | Path) -> Path:
    root = Path(root)
    data = root / "data"
    dist = root / "dist"
    dist.mkdir(parents=True, exist_ok=True)

    kb_meta = _read_json(data / "kb.json", {}).get("meta", {})
    excluded = ((kb_meta.get("stats") or {}).get("policy") or {}).get("excluded_entities") or []

    def redact(text: str) -> str:
        for e in excluded:
            text = text.replace(e, "（作者）")
        return text

    status = _read_json(data / "status.json", {})
    quality = _read_json(data / "quality.json", {})
    selftest = _read_json(data / "selftest.json", {})
    history = _read_jsonl(data / "autopilot.jsonl", 200)
    changelog = _read_jsonl(data / "changelog.jsonl", 30)
    tele = Telemetry(data / "usage.jsonl").stats()

    ok = bool(status.get("ok"))
    badge = f'<span class="badge{"" if ok else " bad"}">{"健康" if ok else "异常"}</span>'

    cards = [
        ("概念", status.get("concepts", "-")),
        ("问答", status.get("faqs", "-")),
        ("关系", status.get("relations", "-")),
        ("引证", status.get("evidence", "-")),
        ("质量错误", (quality.get("counts") or {}).get("error", "-")),
        ("质量警告", (quality.get("counts") or {}).get("warn", "-")),
        ("自测通过", f"{selftest.get('passed', '-')}/{selftest.get('total', '-')}"),
        ("业务问答", tele.get("business", 0)),
        ("命中率", f"{round((tele.get('hit_rate') or 0) * 100)}%"),
        ("技能调用", (tele.get("by_client_kind") or {}).get("skill", 0)),
        ("命令行调用", (tele.get("by_client_kind") or {}).get("shell", 0)),
        ("外部调用", (tele.get("by_origin") or {}).get("external", 0)),
    ]
    cards_html = "".join(
        f'<div class="card"><b>{html.escape(str(v))}</b><span>{html.escape(k)}</span></div>'
        for k, v in cards
    )

    # 巡检时间线
    rows = []
    for item in reversed(history[-20:]):
        rebuilt = "是" if item.get("rebuilt") else "否"
        q = item.get("quality") or {}
        t = item.get("selftest") or {}
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('checked_at', '')))}</td>"
            f"<td>{'✅' if item.get('ok') else '❌'}</td>"
            f"<td>{rebuilt}</td>"
            f"<td>{q.get('errors', '-')}/{q.get('warnings', '-')}</td>"
            f"<td>{t.get('passed', '-')}/{t.get('total', '-')}</td>"
            f"<td>{item.get('duration_ms', '-')} ms</td>"
            "</tr>"
        )
    timeline = (
        "<table><tr><th>时间</th><th>健康</th><th>重建</th><th>质量 错/警</th>"
        "<th>自测</th><th>耗时</th></tr>" + "".join(rows) + "</table>"
        if rows else '<div class="empty">还没有巡检记录。运行一次 mcai autopilot --once。</div>'
    )

    # 变更日志
    change_rows = []
    for entry in reversed(changelog[-10:]):
        parts = []
        if entry.get("added"):
            parts.append("+ " + "、".join(entry["added"][:5]))
        if entry.get("removed"):
            parts.append("− " + "、".join(entry["removed"][:5]))
        if entry.get("changed"):
            parts.append("~ " + "、".join(entry["changed"][:5]))
        change_rows.append(
            f"<tr><td>{html.escape(str(entry.get('ts', '')))}</td>"
            f"<td>{html.escape('；'.join(parts) or '（无术语变化）')}</td></tr>"
        )
    changelog_html = (
        "<table><tr><th>时间</th><th>变化</th></tr>" + "".join(change_rows) + "</table>"
        if change_rows else '<div class="empty">还没有术语变更记录。</div>'
    )

    # 质量明细
    issues = (quality.get("errors") or []) + (quality.get("warnings") or [])
    issue_rows = "".join(
        f"<tr><td>{html.escape(i.get('level', ''))}</td>"
        f"<td>{html.escape(i.get('code', ''))}</td>"
        f"<td>{html.escape(i.get('detail', ''))}</td></tr>"
        for i in issues[:20]
    )
    issues_html = (
        "<table><tr><th>级别</th><th>代码</th><th>说明</th></tr>" + issue_rows + "</table>"
        if issue_rows else '<div class="empty">本轮没有错误或警告。提示项只在 quality.json 里。</div>'
    )

    top_questions = "".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            html.escape(redact(q.get("question", ""))),
            q.get("count", 0),
            html.escape("、".join(c.get("client", "") for c in q.get("clients", [])) or "(未记录)")
            + ("　<b>外部</b>" if q.get("external") else ""),
        )
        for q in tele.get("top_questions", [])[:10]
    ) or '<tr><td colspan="3" class="empty">暂无业务问答</td></tr>'

    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>本地观测台 · 元意识知识库</title>
<style>{CSS}</style></head>
<body><div class="wrap">
  <div class="nav muted"><a href="/index.html">知识库</a><a href="/dashboard.html">观测台</a>
  <a href="/dataset/index.html">数据集</a><a href="/guide.md">接入指南</a></div>
  <h1>本地观测台 {badge}</h1>
  <div class="muted">最近一次检查：{html.escape(str(status.get('checked_at', '尚未运行')))} ·
  服务：{'在线' if status.get('server_ok') else '离线'} ·
  本轮重建：{'是' if status.get('rebuilt') else '否'}</div>

  <div class="cards">{cards_html}</div>

  <h2>调用趋势（近 14 天）</h2>
  {_bars(tele.get('by_day', {}))}
  <div class="muted" style="margin-top:10px">
    健康探测 {tele.get('probes', 0)} 次 ·
    本机 {(tele.get('by_origin') or {}).get('local', 0)} ·
    外部 {(tele.get('by_origin') or {}).get('external', 0)} ·
    未标记 {(tele.get('by_origin') or {}).get('unknown', 0)}<br>
    渠道：{html.escape(str(tele.get('by_channel', {})))} ·
    类型：{html.escape(str(tele.get('by_type', {})))}
  </div>

  <h2>巡检时间线</h2>
  {timeline}

  <h2>质量明细</h2>
  {issues_html}

  <h2>术语变更</h2>
  {changelog_html}

  <h2>高频问题（仅业务问答，不含健康探测）</h2>
  <table><tr><th>问题</th><th>次数</th><th>来源</th></tr>{top_questions}</table>

  <p class="muted" style="margin-top:40px">
    本页由自动驾驶在每次检查后重新生成 · {datetime.now().astimezone().isoformat(timespec='seconds')}
  </p>
</div></body></html>"""

    out = dist / "dashboard.html"
    out.write_text(html_doc, encoding="utf-8")
    return out
