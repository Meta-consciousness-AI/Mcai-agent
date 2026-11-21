#!/usr/bin/env python3
"""MCAI remote knowledge client (stdlib only).

用法:
  python3 mcai_client.py answer "什么是元识？"
  python3 mcai_client.py batch "什么是元识|什么是元知"
  python3 mcai_client.py search "序生" --limit 5
  python3 mcai_client.py concept "元识"
  python3 mcai_client.py related "元识"

环境变量:
  MCAI_BASE_URL  默认 https://mcai-mcp-public-338698-11-1316838521.sh.run.tcloudbase.com/api/v1
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = (
    "https://mcai-mcp-public-338698-11-1316838521.sh.run.tcloudbase.com/api/v1"
)
BASE = os.environ.get("MCAI_BASE_URL", DEFAULT_BASE).rstrip("/")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
TIMEOUT = int(os.environ.get("MCAI_TIMEOUT", "90"))
UA = "mcai-remote-skill/1.0"


def _request(path: str, payload: dict | None = None):
    url = BASE + path
    data = None
    headers = {"User-Agent": UA, "Accept": "application/json", "X-MCAI-Client": "remote-skill"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", "replace")
        return json.loads(raw)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return {"ok": False, "error": f"HTTP {e.code}", "detail": body[:500]}
    except Exception as e:  # network / timeout / JSON
        return {"ok": False, "error": type(e).__name__, "detail": str(e)}


def _search_slug(term: str) -> str | None:
    data = _request("/search?" + urllib.parse.urlencode({"q": term, "limit": 1}))
    results = data.get("results") or []
    if results:
        return results[0].get("slug")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="MCAI remote knowledge client")
    sub = parser.add_subparsers(dest="command", required=True)

    p_answer = sub.add_parser("answer", help="自然语言提问")
    p_answer.add_argument("question")

    p_batch = sub.add_parser("batch", help="多个问题，用 | 分隔")
    p_batch.add_argument("questions")

    p_search = sub.add_parser("search", help="检索术语")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=5)

    p_concept = sub.add_parser("concept", help="取术语完整词条")
    p_concept.add_argument("term")

    p_related = sub.add_parser("related", help="取术语关系子图")
    p_related.add_argument("term")

    args = parser.parse_args()

    if args.command == "answer":
        data = _request("/answer", {"question": args.question})
    elif args.command == "batch":
        questions = [q.strip() for q in args.questions.split("|") if q.strip()]
        if not questions:
            data = {"ok": False, "error": "empty questions"}
        else:
            data = _request("/answer/batch", {"questions": questions})
    elif args.command == "search":
        data = _request(
            "/search?" + urllib.parse.urlencode({"q": args.query, "limit": args.limit})
        )
    elif args.command == "concept":
        slug = _search_slug(args.term)
        data = _request("/concept/" + urllib.parse.quote(slug)) if slug else {
            "ok": False,
            "error": "not_found",
            "detail": f"未找到术语：{args.term}",
        }
    elif args.command == "related":
        data = _request("/related?" + urllib.parse.urlencode({"term": args.term, "depth": 1}))
    else:
        data = {"ok": False, "error": "unknown command"}

    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
