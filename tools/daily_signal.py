# -*- coding: utf-8 -*-
"""每日信号检查：并发查询，逐行输出，最多约 30 秒。

用法：
    python tools/daily_signal.py
"""
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PUB = "https://mcai-mcp-public-338698-11-1316838521.sh.run.tcloudbase.com"
TOK = "https://mcai-mcp-gitee-338698-11-1316838521.sh.run.tcloudbase.com"
TOKEN = "wmRJDHezXcON_8-JxRp4E8ex-wRuGZx1"


TOKEN_FILE = r"E:\th\元意识\元意识资料\Mcai-Agent\mcai-knowledge\Zenodo令牌.txt"


def zenodo_token():
    import os
    tok = os.environ.get("ZENODO_TOKEN", "").strip()
    if tok:
        return tok
    try:
        return Path(TOKEN_FILE).read_text(encoding="utf-8").strip()
    except Exception:
        return ""

ZENODO = {
    "数据集": 23836789,
    "预印本": 23830600,
    "规范V1.1": 23831131,
    "规范V1.3": 23850554,
}


def fetch(url, headers=None, timeout=60, tries=2):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")
        except Exception as e:
            last = e
    raise last


def local_version():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    return m.group(1) if m else "?"


def check_mcp_health(name, base):
    try:
        d = json.loads(fetch(base + "/api/v1/health"))
        return f"MCP {name}：{d.get('version', '?')}", None
    except Exception as e:
        return f"MCP {name}：查询失败（{type(e).__name__}）", None


def check_usage(name, base, hdr):
    try:
        d = json.loads(fetch(base + "/api/v1/usage", hdr))
        by = d.get("by_action") or {}
        biz = {k: v for k, v in by.items() if k != "health"}
        if biz:
            return f"调用 {name}：{biz}", f"{name}实例出现业务调用 {biz}"
        return f"调用 {name}：无业务调用", None
    except Exception as e:
        return f"调用 {name}：查询失败（{type(e).__name__}）", None


def check_pypi(lv):
    try:
        d = json.loads(fetch("https://pypi.org/pypi/mcai-knowledge/json"))
        v = d["info"]["version"]
        return f"PyPI：{v}", (f"PyPI {v} ≠ 本地 {lv}" if v != lv else None)
    except Exception as e:
        return f"PyPI：查询失败（{type(e).__name__}）", None


def check_registry(lv):
    try:
        d = json.loads(fetch("https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.Meta-consciousness-AI/mcai-knowledge"))
        ss = d.get("servers") or []
        vers = sorted({x.get("server", x).get("version", "") for x in ss})
        v = vers[-1] if vers else "?"
        return f"注册表：{v}", (f"注册表 {v} ≠ 本地 {lv}" if v != lv else None)
    except Exception as e:
        return f"注册表：查询失败（{type(e).__name__}）", None


def check_glama(lv):
    try:
        t = fetch("https://glama.ai/mcp/servers/Meta-consciousness-AI/Mcai-agent")
        v = lv if lv in t else "未知"
        return f"Glama：{v}", None
    except Exception as e:
        return f"Glama：查询失败（{type(e).__name__}）", None


def check_github():
    try:
        t = fetch("https://github.com/Meta-consciousness-AI/Mcai-agent")
        m = re.search(r'"stargazerCount":(\d+)', t)
        f = re.search(r'"forksCount":(\d+)', t)
        s = m.group(1) if m else "?"
        return f"GitHub：{s} Star / {f.group(1) if f else '?'} Fork", (f"GitHub Star 变为 {s}" if s not in ("?", "0") else None)
    except Exception as e:
        return f"GitHub：查询失败（{type(e).__name__}）", None


def check_zenodo_one(name, rid):
    tok = zenodo_token()
    if tok:
        try:
            raw = fetch(f"https://zenodo.org/api/records/{rid}",
                        headers={"User-Agent": "mcai-signal", "Authorization": "Bearer " + tok})
            st = json.loads(raw).get("stats", {})
            return f"Zenodo {name}：{st.get('views', '?')} 浏览 / {st.get('downloads', '?')} 下载", None
        except Exception:
            pass
    try:
        t = fetch(f"https://zenodo.org/records/{rid}")
        v = int((re.findall(r'"views":\s*(\d+)', t) or [0])[0])
        d = int((re.findall(r'"downloads":\s*(\d+)', t) or [0])[0])
        return f"Zenodo {name}：{v} 浏览 / {d} 下载", None
    except Exception as e:
        return f"Zenodo {name}：查询失败（{type(e).__name__}）", None


def main():
    lv = local_version()
    print(f"本地版本：{lv}")
    print("查询中……可能较慢（含冷启动），请耐心等待；按 Ctrl+C 可中断")

    tasks = [
        ("MCP 公开", lambda: check_mcp_health("公开", PUB)),
        ("MCP 令牌", lambda: check_mcp_health("令牌", TOK)),
        ("调用 公开", lambda: check_usage("公开", PUB, None)),
        ("调用 令牌", lambda: check_usage("令牌", TOK, {"Authorization": "Bearer " + TOKEN})),
        ("PyPI", lambda: check_pypi(lv)),
        ("注册表", lambda: check_registry(lv)),
        ("Glama", lambda: check_glama(lv)),
        ("GitHub", lambda: check_github()),
        *[(f"Zenodo {n}", (lambda n=n, r=r: check_zenodo_one(n, r))) for n, r in ZENODO.items()],
    ]

    changed = []
    with ThreadPoolExecutor(max_workers=9) as ex:
        futures = {ex.submit(fn): name for name, fn in tasks}
        for fut in as_completed(futures):
            try:
                line, chg = fut.result()
            except Exception as e:
                line, chg = f"{futures[fut]}：异常（{type(e).__name__}）", None
            print(line, flush=True)
            if chg:
                changed.append(chg)

    print("-" * 40)
    if changed:
        print("结论：有变化，需要人工看：")
        for c in changed:
            print("  - " + c)
        return 1
    print("结论：今日无真实调用信号。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
