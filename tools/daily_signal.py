# -*- coding: utf-8 -*-
"""每日信号检查：并发查询，逐行输出。

改进（2026-11-18）：
- 详细错误：显示 HTTP 状态码，区分限流/超时/连接失败；
- 自动重试：403/429/5xx 与超时按指数退避重试；
- GitHub 改用 api.github.com（网页版常被阻断）；
- Zenodo 串行 + 间隔，避免触发限流；
- 失败时显示上次成功值，趋势不中断；
- 支持 --only 过滤、--verbose 细节、--no-cache。

用法：
    python tools/daily_signal.py
    python tools/daily_signal.py --only zenodo
    python tools/daily_signal.py --verbose
"""
import argparse
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PUB = "https://mcai-mcp-public-338698-11-1316838521.sh.run.tcloudbase.com"
TOK = "https://mcai-mcp-gitee-338698-11-1316838521.sh.run.tcloudbase.com"
TOKEN = "wmRJDHezXcON_8-JxRp4E8ex-wRuGZx1"
SIGNALS = ROOT / "data" / "signals.jsonl"
CACHE = ROOT / "data" / "signal_last.json"

TOKEN_FILE = r"E:\th\元意识\元意识运营\Mcai-Agent\mcai-knowledge\Zenodo令牌.txt"

# 每个概念只取一条代表记录：Zenodo 的 stats 按 concept 聚合，取多个版本会重复计数
ZENODO = {
    "数据集": 24191734,
    "预印本": 23830600,
    "规范": 23850554,
}

RETRY_CODES = {403, 429, 500, 502, 503, 504}


def zenodo_token():
    import os
    tok = os.environ.get("ZENODO_TOKEN", "").strip()
    if tok:
        return tok
    try:
        return Path(TOKEN_FILE).read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def fmt_err(e, verbose=False):
    """把异常变成一句可读的原因。"""
    if isinstance(e, urllib.error.HTTPError):
        code = e.code
        if code in (403, 429):
            return f"HTTP {code}（限流）"
        if 500 <= code < 600:
            return f"HTTP {code}（服务端错误）"
        return f"HTTP {code}"
    if isinstance(e, (socket.timeout, TimeoutError)):
        return "超时"
    if isinstance(e, urllib.error.URLError):
        reason = getattr(e, "reason", e)
        if isinstance(reason, (socket.timeout, TimeoutError)) or "timed out" in str(reason):
            return "超时"
        return f"连接失败（{type(reason).__name__}）"
    return f"{type(e).__name__}" + (f": {e}" if verbose else "")


def fetch(url, headers=None, timeout=30, tries=3, backoff=1.0):
    hdrs = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    if headers:
        hdrs.update(headers)
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = e
            if e.code in RETRY_CODES and attempt < tries - 1:
                time.sleep(backoff * (2 ** attempt))
                continue
            raise
        except Exception as e:
            last = e
            if attempt < tries - 1:
                time.sleep(backoff * (2 ** attempt))
                continue
            raise
    raise last


def load_cache():
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache):
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def with_last(cache, key, line, ok, value=None):
    """成功则更新缓存；失败则附上上次成功的值。"""
    if ok:
        if value is not None:
            cache[key] = {"value": value, "ts": time.strftime("%Y-%m-%d %H:%M")}
        return line
    prev = cache.get(key)
    if prev:
        return f"{line}（上次 {prev['ts']}：{prev['value']}）"
    return line


def local_version():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    return m.group(1) if m else "?"


def check_mcp_health(name, base):
    try:
        d = json.loads(fetch(base + "/api/v1/health", timeout=90, tries=3))
        v = d.get("version", "?")
        return f"MCP {name}：{v}", True, v
    except Exception as e:
        return f"MCP {name}：查询失败（{fmt_err(e)}）", False, None


def check_usage(name, base, hdr):
    try:
        d = json.loads(fetch(base + "/api/v1/usage", hdr, timeout=90, tries=3))
        by = d.get("by_action") or {}
        biz = {k: v for k, v in by.items() if k != "health"}
        if biz:
            return f"调用 {name}：{biz}", True, None
        return f"调用 {name}：无业务调用", True, None
    except Exception as e:
        return f"调用 {name}：查询失败（{fmt_err(e)}）", False, None


def check_pypi(lv):
    try:
        d = json.loads(fetch("https://pypi.org/pypi/mcai-knowledge/json", timeout=30))
        v = d["info"]["version"]
        return f"PyPI：{v}", True, v
    except Exception as e:
        return f"PyPI：查询失败（{fmt_err(e)}）", False, None


def check_registry(lv):
    try:
        d = json.loads(fetch(
            "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.Meta-consciousness-AI/mcai-knowledge",
            timeout=30))
        ss = d.get("servers") or []
        vers = sorted({x.get("server", x).get("version", "") for x in ss})
        v = vers[-1] if vers else "?"
        return f"注册表：{v}", True, v
    except Exception as e:
        return f"注册表：查询失败（{fmt_err(e)}）", False, None


def check_glama(lv):
    try:
        t = fetch("https://glama.ai/mcp/servers/Meta-consciousness-AI/Mcai-agent", timeout=30)
        v = lv if lv in t else "未知"
        return f"Glama：{v}", True, v
    except Exception as e:
        return f"Glama：查询失败（{fmt_err(e)}）", False, None


def check_github():
    """用 api.github.com：网页版在部分网络下会超时。"""
    try:
        d = json.loads(fetch("https://api.github.com/repos/Meta-consciousness-AI/mcai-agent", timeout=30))
        s = d.get("stargazers_count", 0)
        f = d.get("forks_count", 0)
        line = f"GitHub：{s} Star / {f} Fork"
        return line, True, f"{s}/{f}"
    except Exception as e:
        return f"GitHub：查询失败（{fmt_err(e)}）", False, None


def check_zenodo_one(name, rid):
    tok = zenodo_token()
    hdr = {"Authorization": "Bearer " + tok} if tok else None
    try:
        raw = fetch(f"https://zenodo.org/api/records/{rid}", hdr, timeout=30, tries=2, backoff=3.0)
        d = json.loads(raw)
        st = d.get("stats") or {}
        v, dl = st.get("views"), st.get("downloads")
        if v is None or dl is None:
            raise ValueError("stats missing")
        uv, ud = st.get("unique_views"), st.get("unique_downloads")
        extra = f"（独立 {uv}/{ud}）" if uv is not None and ud is not None else ""
        return f"Zenodo {name}：{v} 浏览 / {dl} 下载{extra}", True, f"{v}/{dl}"
    except Exception as e1:
        try:
            t = fetch(f"https://zenodo.org/records/{rid}", timeout=30, tries=1, backoff=2.0)
            v = int((re.findall(r'"views":\s*(\d+)', t) or [0])[0])
            d = int((re.findall(r'"downloads":\s*(\d+)', t) or [0])[0])
            return f"Zenodo {name}：{v} 浏览 / {d} 下载", True, f"{v}/{d}"
        except Exception as e2:
            return f"Zenodo {name}：查询失败（{fmt_err(e2)}）", False, None


def _last_total(instance: str) -> int:
    if not SIGNALS.exists():
        return 0
    last = 0
    for line in SIGNALS.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except Exception:
            continue
        if row.get("instance") == instance:
            last = max(last, int(row.get("total", 0)))
    return last


def record_usage():
    rows = []
    for name, base in (("public", PUB), ("gitee", TOK)):
        try:
            d = json.loads(fetch(base + "/api/v1/usage", {"Authorization": "Bearer " + TOKEN},
                                 timeout=90, tries=3))
        except Exception:
            continue
        total = int(d.get("total_calls", 0))
        prev = _last_total(name)
        rows.append({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "instance": name,
            "total": total,
            "business": int(d.get("business_calls", 0)),
            "by_action": d.get("by_action") or {},
            "reset": total < prev,
        })
    if not rows:
        print("计数快照：两个实例都没读到")
        return
    SIGNALS.parent.mkdir(parents=True, exist_ok=True)
    with SIGNALS.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"计数快照：已写入 {len(rows)} 条 -> {SIGNALS.relative_to(ROOT)}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="只跑名称包含该词的项，例如 zenodo / 调用 / github")
    ap.add_argument("--verbose", action="store_true", help="打印完整异常信息")
    ap.add_argument("--no-cache", action="store_true", help="不读也不写上次缓存")
    args = ap.parse_args(argv)

    lv = local_version()
    print(f"本地版本：{lv}")
    print("查询中……可能较慢（含冷启动），请耐心等待；按 Ctrl+C 可中断")

    fast = [
        ("MCP 公开", lambda: check_mcp_health("公开", PUB)),
        ("MCP 令牌", lambda: check_mcp_health("令牌", TOK)),
        ("调用 公开", lambda: check_usage("公开", PUB, None)),
        ("调用 令牌", lambda: check_usage("令牌", TOK, {"Authorization": "Bearer " + TOKEN})),
        ("PyPI", lambda: check_pypi(lv)),
        ("注册表", lambda: check_registry(lv)),
        ("Glama", lambda: check_glama(lv)),
        ("GitHub", lambda: check_github()),
    ]

    cache = {} if args.no_cache else load_cache()
    changed = []

    def run(name, fn):
        try:
            line, ok, val = fn()
        except Exception as e:
            line, ok, val = f"{name}：异常（{fmt_err(e, args.verbose)}）", False, None
        key = name
        line = with_last(cache, key, line, ok, val)
        return name, line

    fast = [(n, f) for n, f in fast if args.only in n] if args.only else fast
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(run, n, f): n for n, f in fast}
        for fut in as_completed(futures):
            name, line = fut.result()
            print(line, flush=True)
            if "变为" in line or "≠" in line:
                changed.append(line)

    # Zenodo 串行，避免限流；一旦遇到限流就停止本轮剩余项
    zitems = [(n, r) for n, r in ZENODO.items() if not args.only or args.only in f"zenodo{n}"]
    for i, (n, r) in enumerate(zitems):
        name, line = run(f"Zenodo {n}", lambda n=n, r=r: check_zenodo_one(n, r))
        print(line, flush=True)
        if "限流" in line:
            print("Zenodo 触发限流，本轮跳过其余记录", flush=True)
            break
        if i < len(zitems) - 1:
            time.sleep(2.0)

    if not args.no_cache:
        save_cache(cache)

    try:
        record_usage()
    except Exception as e:
        print(f"计数快照失败（{fmt_err(e)}）")

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
