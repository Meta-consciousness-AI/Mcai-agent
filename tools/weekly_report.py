"""生成一份可填写的周报：自动统计调用日志与仓库状态，平台数据留空待填。"""
from __future__ import annotations

import json
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "usage.jsonl"
OUT_DIR = ROOT / "docs"


def fetch_json(url: str) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mcai-weekly"})
        return json.load(urllib.request.urlopen(req, timeout=20))
    except Exception:
        return None


def usage_stats(days: int = 7) -> dict:
    since = datetime.now().astimezone() - timedelta(days=days)
    by_action = Counter()
    by_channel = Counter()
    by_day = Counter()
    total = 0
    if DATA.exists():
        for line in DATA.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = row.get("ts", "")
            try:
                when = datetime.fromisoformat(ts)
            except ValueError:
                continue
            if when < since:
                continue
            action = row.get("action", "")
            if action in ("health", "stats", "gaps", "rebuild"):
                continue
            total += 1
            by_action[action] += 1
            by_channel[row.get("channel", "")] += 1
            by_day[when.strftime("%Y-%m-%d")] += 1
    return {"total": total, "by_action": by_action, "by_channel": by_channel, "by_day": by_day}


def remote_usage() -> dict | None:
    import os
    url = os.environ.get("MCAI_USAGE_URL", "").strip()
    token = os.environ.get("MCAI_TOKEN", "").strip()
    if not url or not token:
        return None
    import time
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
            return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception:
            if attempt == 2:
                return None
            time.sleep(3)


def repo_stats() -> dict:
    repo = fetch_json("https://api.github.com/repos/Meta-consciousness-AI/mcai-agent") or {}
    pkg = fetch_json("https://pypi.org/pypi/mcai-knowledge/json") or {}
    version = (pkg.get("info") or {}).get("version", "")
    released = ""
    if version:
        files = (pkg.get("releases") or {}).get(version) or []
        if files:
            released = files[0].get("upload_time_iso_8601", "")[:10]
    return {
        "stars": repo.get("stargazers_count", "-"),
        "forks": repo.get("forks_count", "-"),
        "issues": repo.get("open_issues_count", "-"),
        "version": version or "-",
        "released": released or "-",
    }


def build() -> Path:
    today = date.today()
    stats = usage_stats(7)
    repo = repo_stats()
    remote = remote_usage()

    lines = [
        f"# 周报 {today.isoformat()}",
        "",
        "> 自动生成部分来自本地 `data/usage.jsonl` 与 GitHub / PyPI；平台数据需手动填写。",
        "",
        "## 一、机器调用（近 7 天，已排除健康检查）",
        "",
        f"- 总调用：**{stats['total']}** 次",
    ]
    if stats["by_action"]:
        lines += ["", "| 工具 / 动作 | 次数 |", "|---|---|"]
        lines += [f"| {k} | {v} |" for k, v in stats["by_action"].most_common()]
    if stats["by_channel"]:
        lines += ["", "| 渠道 | 次数 |", "|---|---|"]
        lines += [f"| {k or '未知'} | {v} |" for k, v in stats["by_channel"].most_common()]
    if stats["by_day"]:
        lines += ["", "| 日期 | 次数 |", "|---|---|"]
        lines += [f"| {k} | {v} |" for k, v in sorted(stats["by_day"].items())]
    if not stats["total"]:
        lines += ["", "近 7 天没有记录到真实调用（只有健康检查或本地测试）。"]

    lines += ["", "### 远程 MCP 服务"]
    if remote:
        lines.append(f"- 累计调用：**{remote.get('total_calls', '-')}** 次（其中 MCP {remote.get('mcp_calls', '-')} 次、业务 {remote.get('business_calls', '-')} 次）")
        lines.append(f"- 最近调用：{remote.get('last_call', '-') or '无'}")
        by_day = remote.get("by_day") or {}
        if by_day:
            lines += ["", "| 日期 | 次数 |", "|---|---|"]
            lines += [f"| {k} | {v} |" for k, v in sorted(by_day.items())[-14:]]
    else:
        lines.append("- 未配置 `MCAI_USAGE_URL` / `MCAI_TOKEN`，本次未拉取；可在命令行临时设置后重跑。")

    lines += [
        "",
        "## 二、仓库与包",
        "",
        f"- GitHub Star：{repo['stars']} · Fork：{repo['forks']} · 开放 Issue：{repo['issues']}",
        f"- PyPI 最新版本：{repo['version']}（{repo['released']}）",
        "",
        "## 三、内容平台（手动填写）",
        "",
        "| 平台 | 阅读 / 播放 | 互动 | 备注 |",
        "|---|---|---|---|",
        "| 公众号 |  |  | 阅读原文点击 |",
        "| 知乎 |  |  |  |",
        "| 掘金 |  |  |  |",
        "| 微博 |  |  |  |",
        "| 小红书 |  |  | 赞藏 |",
        "| 视频号 |  |  |  |",
        "| 抖音 |  |  | 完播率 |",
        "| 快手 |  |  |  |",
        "| 腾讯视频 |  |  |  |",
        "| 爱奇艺 |  |  |  |",
        "",
        "## 四、收录与引用",
        "",
        "- mcprush：已认领",
        "- PhilArchive：已收录",
        "- 其他第三方引用：",
        "",
        "## 五、判断",
        "",
        "1. 本周真实调用：",
        "2. 内容带来的站点访问：",
        "3. 是否出现第三方引用或案例：",
        "",
        "> 三个数不动，扩渠道不是重点。",
        "",
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"周报-{today.isoformat()}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


if __name__ == "__main__":
    print(build())
