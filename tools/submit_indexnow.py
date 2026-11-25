# -*- coding: utf-8 -*-
"""把 dist/sitemap.xml 里的全部 URL 通过 IndexNow 一次性提交。

IndexNow 是「主动告诉搜索引擎有新页面」的开放协议：站点根下放一个 ``<key>.txt``
证明域名归属，然后 POST 一份 URL 列表即可，不需要登录任何平台。

执行顺序（``dist/`` 是构建产物，重建会清掉，所以验证文件必须在构建之后再补）：

1. ``python tools/build_site_from_kb.py``        重新生成 dist/（含 sitemap.xml）
2. ``python tools/submit_indexnow.py --write-key``  写 dist/<key>.txt
3. ``python tools/submit_indexnow.py``            真正提交
4. 部署 dist/（CloudBase，用户窗口执行）

用法：

    python tools/submit_indexnow.py --dry-run
    python tools/submit_indexnow.py --write-key
    python tools/submit_indexnow.py [--endpoint URL]

key 存在 ``config/indexnow.json``（``{"key": "..."}``），不存在时自动生成一个
32 位十六进制串并写入。**key 是公开信息**（会随 ``<key>.txt`` 一起发布），不是秘密。
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SITEMAP = DIST / "sitemap.xml"
KEY_CONFIG = ROOT / "config" / "indexnow.json"
DEFAULT_ENDPOINT = "https://api.indexnow.org/indexnow"
BATCH_MAX = 10000
TIMEOUT = 30


def _safe_stdio() -> None:
    """GBK 控制台下不因个别字符编码失败而 traceback（与 mcai CLI 同一做法）。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass


def load_or_create_key() -> str:
    """读 config/indexnow.json 里的 key；没有就生成 32 位十六进制串并写回。"""
    if KEY_CONFIG.exists():
        try:
            data = json.loads(KEY_CONFIG.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SystemExit(f"[FAIL] 读不了 {KEY_CONFIG}：{exc}")
        key = str((data or {}).get("key") or "").strip()
        if key:
            return key
    key = secrets.token_hex(16)
    KEY_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    KEY_CONFIG.write_text(json.dumps({"key": key}, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] 已生成 key 并写入 {KEY_CONFIG}")
    return key


def write_key_file(key: str) -> Path:
    """把 key 写成 dist/<key>.txt（内容就是 key，末尾带换行），可重复执行。"""
    if not DIST.is_dir():
        raise SystemExit(f"[FAIL] 没有 {DIST}，先跑 python tools/build_site_from_kb.py")
    path = DIST / f"{key}.txt"
    # 按字节写，固定成 key + 单个 LF（不随平台变成 CRLF），保证内容可复现。
    path.write_bytes(key.encode("ascii") + b"\n")
    return path


def read_urls() -> list[str]:
    """按文档顺序取 sitemap 里的全部 <loc>。"""
    if not SITEMAP.exists():
        raise SystemExit(f"[FAIL] 没有 {SITEMAP}，先跑 python tools/build_site_from_kb.py")
    try:
        tree = ElementTree.parse(SITEMAP)
    except ElementTree.ParseError as exc:
        raise SystemExit(f"[FAIL] sitemap 解析失败：{exc}")
    urls = [elem.text.strip() for elem in tree.iter() if elem.tag.endswith("loc") and elem.text]
    return [url for url in urls if url]


def site_host(urls: list[str]) -> str:
    """从 sitemap 的第一条 url 取 host；顺带确认全部同域，避免 keyLocation 对不上。"""
    if not urls:
        raise SystemExit("[FAIL] sitemap 里没有 <loc>")
    host = urlsplit(urls[0]).netloc
    if not host:
        raise SystemExit(f"[FAIL] 取不到 host：{urls[0]}")
    odd = [url for url in urls if urlsplit(url).netloc != host]
    if odd:
        raise SystemExit(f"[FAIL] sitemap 里混入了其它 host（{odd[0]}），先查构建")
    return host


def build_payload(host: str, key: str, urls: list[str]) -> dict:
    return {
        "host": host,
        "key": key,
        "keyLocation": f"https://{host}/{key}.txt",
        "urlList": urls,
    }


def report(status: int, body: bytes, count: int) -> int:
    """按状态码给出固定文案；非 2xx 时附响应正文前几行。"""
    if status in (200, 202):
        print(f"[OK] IndexNow 已接收：status={status} urls={count}")
        return 0
    if status == 403:
        print("[FAIL] 403 key 校验失败：keyLocation 是否可访问、内容是否与 key 完全一致")
    elif status == 422:
        print("[FAIL] 422 URL 不属于该 host")
    elif status == 429:
        print("[FAIL] 429 请求过快，稍后再试")
    else:
        print(f"[FAIL] 非 2xx：status={status} urls={count}")
    text = (body or b"").decode("utf-8", "replace").strip()
    for line in text.splitlines()[:5]:
        print("  " + line)
    return 1


def submit(endpoint: str, payload: dict) -> int:
    """POST 一次；返回进程退出码。"""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    count = len(payload["urlList"])
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return report(getattr(resp, "status", 200), resp.read(), count)
    except urllib.error.HTTPError as exc:
        return report(exc.code, exc.read(), count)
    except urllib.error.URLError as exc:
        print(f"[FAIL] 连不上 {endpoint}：{exc.reason}")
        return 1


def main(argv: list[str] | None = None) -> int:
    _safe_stdio()
    parser = argparse.ArgumentParser(description="把 dist/sitemap.xml 的 URL 提交给 IndexNow")
    parser.add_argument("--dry-run", action="store_true", help="只打印数量与首尾各 2 条，不联网")
    parser.add_argument("--write-key", action="store_true", help="只写 dist/<key>.txt，不提交")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help=f"提交地址（默认 {DEFAULT_ENDPOINT}）")
    args = parser.parse_args(argv)

    key = load_or_create_key()
    print(f"key: {key}（{KEY_CONFIG}）")

    if args.write_key:
        path = write_key_file(key)
        print(f"[OK] 已写 {path}")
        return 0

    urls = read_urls()
    host = site_host(urls)
    print(f"host: {host}")
    print(f"urls: {len(urls)}")

    if args.dry_run:
        head = urls[:2]
        tail = urls[-2:] if len(urls) > 2 else []
        for url in head + tail:
            print("  " + url)
        print(f"[OK] dry-run：将提交 {len(urls)} 条给 {args.endpoint}（未联网）")
        return 0

    batches = [urls[i:i + BATCH_MAX] for i in range(0, len(urls), BATCH_MAX)]
    code = 0
    for index, batch in enumerate(batches, 1):
        if len(batches) > 1:
            print(f"第 {index}/{len(batches)} 批：{len(batch)} 条")
        code = submit(args.endpoint, build_payload(host, key, batch))
        if code != 0:
            break
    return code


if __name__ == "__main__":
    sys.exit(main())
