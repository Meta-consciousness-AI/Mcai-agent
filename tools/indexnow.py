"""IndexNow 提交：把 sitemap 里的 URL 推给 Bing / Yandex 等。

用法：
    python tools/indexnow.py            # 生成/复用 key，写验证文件，提交全部 URL
    python tools/indexnow.py --write-key  # 只写验证文件
"""
from __future__ import annotations

import json
import re
import secrets
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
KEY_FILE = ROOT / "data" / "indexnow-key.txt"
SITE = "https://mcai-knowledge-d7gtizltz910e2269-1316838521.tcloudbaseapp.com"
HOST = "mcai-knowledge-d7gtizltz910e2269-1316838521.tcloudbaseapp.com"


def get_key() -> str:
    if KEY_FILE.exists():
        key = KEY_FILE.read_text(encoding="utf-8").strip()
        if len(key) >= 8:
            return key
    key = secrets.token_hex(16)
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_text(key, encoding="utf-8")
    return key


def write_key_file(key: str) -> Path:
    path = DIST / f"{key}.txt"
    path.write_text(key, encoding="utf-8")
    return path


def urls_from_sitemap() -> list[str]:
    xml = (DIST / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def submit(key: str, urls: list[str]) -> int:
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": f"{SITE}/{key}.txt",
        "urlList": urls,
    }
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        print("status:", resp.status, "| urls:", len(urls))
        return resp.status


def main() -> int:
    key = get_key()
    path = write_key_file(key)
    print("key file:", path)
    print("key location:", f"{SITE}/{key}.txt")
    urls = urls_from_sitemap()
    if not urls:
        print("sitemap 为空")
        return 1
    return 0 if submit(key, urls) in (200, 202) else 1


if __name__ == "__main__":
    raise SystemExit(main())
