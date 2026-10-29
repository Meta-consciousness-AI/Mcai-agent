"""调用遥测：记录谁在问什么、哪些问题没答上来。

作用有两个：
1. 证明「被调用」——调用量、渠道、问题分布；
2. 驱动补词——未命中的问题会进入 gaps 列表，成为下一轮词条/问答的输入。
"""
from __future__ import annotations

import json
import threading
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

PROBE_ACTIONS = {"health", "stats", "gaps"}
BUSINESS_ACTIONS = {"answer", "answer_batch", "search", "concept", "related",
                    "mcai_answer", "mcai_concept", "mcai_search", "mcai_related", "mcai_list"}

_lock = threading.Lock()
_instances: dict[str, "Telemetry"] = {}


class Telemetry:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, channel: str, action: str, query: str = "", result_type: str = "",
               ok: bool = True, ms: int = 0, detail: dict | None = None) -> None:
        entry = {
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "channel": channel,
            "action": action,
            "query": (query or "")[:200],
            "type": result_type,
            "ok": ok,
            "ms": ms,
        }
        if detail:
            entry["detail"] = detail
        with _lock:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def entries(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    def stats(self, days: int = 14) -> dict:
        rows = self.entries()
        today = date.today()
        window = [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]
        by_day = Counter()
        for r in rows:
            day = (r.get("ts") or "")[:10]
            if day in window:
                by_day[day] += 1
        answers = [r for r in rows if r.get("action") == "answer"]
        origin = Counter()
        for r in rows:
            origin[self._origin(r)] += 1

        question_rows: dict[str, list[dict]] = {}
        for r in answers:
            q = (r.get("query") or "").strip()
            if q:
                question_rows.setdefault(q, []).append(r)
        top_questions = []
        for q, items in sorted(question_rows.items(), key=lambda kv: -len(kv[1]))[:10]:
            clients = Counter(((i.get("detail") or {}).get("client") or "(未记录)") for i in items)
            top_questions.append({
                "question": q,
                "count": len(items),
                "clients": [{"client": c, "count": n} for c, n in clients.most_common(3)],
                "external": any(self._origin(i) == "external" for i in items),
            })

        batch_rows = [r for r in rows if r.get("action") == "answer_batch"]
        batch_types = [
            t for r in batch_rows for t in ((r.get("detail") or {}).get("types") or [])
        ]
        single_types = [r.get("type") for r in answers if r.get("type")]
        all_types = single_types + batch_types
        hits = sum(1 for t in all_types if t in ("concept", "faq", "relation", "multi"))

        kind_business = Counter(
            self._client_kind(r) for r in rows if r.get("action") in BUSINESS_ACTIONS
        )

        return {
            "total": len(rows),
            "by_client_kind": dict(kind_business),
            "answers": len(answers),
            "business": sum(1 for r in rows if r.get("action") in BUSINESS_ACTIONS),
            "batch_calls": len(batch_rows),
            "batch_answers": len(batch_types),
            "batch_by_type": dict(Counter(batch_types)),
            "hit_rate": round(hits / len(all_types), 3) if all_types else 0,
            "probes": sum(1 for r in rows if r.get("action") in PROBE_ACTIONS),
            "by_origin": dict(origin),
            "by_channel": dict(Counter(r.get("channel", "") for r in rows)),
            "by_action": dict(Counter(r.get("action", "") for r in rows).most_common(10)),
            "by_type": dict(Counter(r.get("type", "") for r in answers).most_common()),
            "by_day": {d: by_day.get(d, 0) for d in window},
            "top_questions": top_questions,
            "last_call": rows[-1]["ts"] if rows else "",
        }

    @staticmethod
    def _client_kind(row: dict) -> str:
        """按客户端标识区分：自检脚本 / 命令行 / 浏览器 / MCP / 其他。"""
        if row.get("channel") == "mcp":
            return "mcp"
        ua = ((row.get("detail") or {}).get("client") or "").lower()
        if "mcai-skill" in ua:
            return "skill"
        if "python-urllib" in ua or "mcai-doctor" in ua:
            return "self"
        if "powershell" in ua or ua.startswith("curl/"):
            return "shell"
        if "mozilla" in ua:
            return "browser"
        return "other"

    @staticmethod
    def _origin(row: dict) -> str:
        """判断调用来自本机自检还是外部。"""
        if row.get("channel") == "mcp":
            return "local"  # MCP 走 stdio，只能在同机运行
        ip = (row.get("detail") or {}).get("ip")
        if not ip:
            return "unknown"  # 早期记录没有 IP 字段
        return "local" if ip in ("127.0.0.1", "::1", "0:0:0:0:0:0:0:1") else "external"

    def gaps(self, limit: int = 20) -> list[dict]:
        rows = [r for r in self.entries() if r.get("type") in ("none", "related") and r.get("query")]
        counter = Counter(r["query"] for r in rows)
        last = {}
        for r in rows:
            last[r["query"]] = r.get("ts", "")
        return [
            {"query": q, "count": n, "last_seen": last.get(q, ""), "type": next(
                (r.get("type") for r in reversed(rows) if r["query"] == q), "")}
            for q, n in counter.most_common(limit)
        ]


def for_root(root: str | Path) -> Telemetry:
    key = str(Path(root).resolve())
    if key not in _instances:
        _instances[key] = Telemetry(Path(root) / "data" / "usage.jsonl")
    return _instances[key]
