"""Web 服务：静态站 + 问答 API，带鉴权、限流、CORS 与访问日志。

设计原则：
- 静态页面公开（让搜索引擎与 AI 爬虫能读），API 可选令牌保护；
- 重建、统计、缺口清单只允许本机访问（防远程误操作与信息泄露）；
- 所有响应带 CORS 头，所有请求写访问日志（不含令牌）。
"""
from __future__ import annotations

import hmac
import json
import mimetypes
import threading
import time
import urllib.parse
import uuid
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import knowledge, pipeline, telemetry

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".jsonl": "application/x-ndjson; charset=utf-8",
    ".csv": "text/csv; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".xml": "application/xml; charset=utf-8",
}

# 只允许本机访问的路径：重建、统计、缺口
LOCAL_ONLY = ("/api/rebuild", "/api/v1/stats", "/api/v1/gaps")
# 无需令牌即可访问（存活探针）
PUBLIC_API = ("/api/v1/health",)


def is_local_ip(ip: str) -> bool:
    return ip in ("127.0.0.1", "::1", "localhost", "0:0:0:0:0:0:0:1")


class RateLimiter:
    """按 key（通常是 IP）的滑动窗口限流。"""

    def __init__(self, limit: int = 60, window: float = 60.0):
        self.limit = max(1, int(limit))
        self.window = float(window)
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._hits.setdefault(key, deque())
            while bucket and now - bucket[0] > self.window:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return False
            bucket.append(now)
            # 防止字典无限增长
            if len(self._hits) > 4096:
                for k in list(self._hits)[:1024]:
                    if not self._hits[k]:
                        self._hits.pop(k, None)
            return True


class Handler(BaseHTTPRequestHandler):
    root: Path
    token: str = ""
    limiter: RateLimiter = RateLimiter(60)
    cors_origin: str = "*"
    lock = threading.Lock()
    access_lock = threading.Lock()

    # ---------- 基础设施 ----------
    def log_message(self, fmt: str, *args) -> None:
        return

    def log_request(self, code="-", size="-") -> None:
        """写访问日志：不含令牌，只记客户端标识。"""
        try:
            ip = self.client_address[0]
            # 经过隧道/反向代理时，记录真实来源
            forwarded = (self.headers.get("CF-Connecting-IP")
                         or (self.headers.get("X-Forwarded-For") or "").split(",")[0].strip())
            if forwarded:
                ip = forwarded
            ms = int((time.monotonic() - getattr(self, "_t0", time.monotonic())) * 1000)
            entry = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "ip": ip,
                "method": getattr(self, "command", ""),
                "path": getattr(self, "path", ""),
                "status": int(code) if isinstance(code, int) or str(code).isdigit() else 0,
                "ms": ms,
                "client": self._client_label(),
            }
            log_path = self.root / "data" / "access.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.access_lock:
                with log_path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001 - 日志失败不影响响应
            pass

    def _client_label(self) -> str:
        raw = self.headers.get("X-MCAI-Client") or self.headers.get("User-Agent") or ""
        return raw.strip()[:80]

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", self.cors_origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-MCAI-Client")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _send_json(self, data: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", MIME[".json"])
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        try:
            body = path.read_bytes()
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        ctype = MIME.get(path.suffix.lower()) or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _deny(self, status: int, message: str) -> None:
        self._send_json({"ok": False, "error": message}, status)

    # ---------- 鉴权 / 限流 ----------
    def _rate_ok(self) -> bool:
        return self.limiter.allow(self.client_address[0])

    def _authorized(self, route: str) -> bool:
        if not self.token:
            return True
        if route in PUBLIC_API:
            return True
        header = self.headers.get("Authorization", "")
        scheme, _, value = header.partition(" ")
        return scheme.lower() == "bearer" and hmac.compare_digest(value.strip(), self.token)

    def do_OPTIONS(self) -> None:
        self._t0 = time.monotonic()
        self.send_response(HTTPStatus.NO_CONTENT)
        self._cors()
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    # ---------- 路由 ----------
    def do_GET(self) -> None:
        self._t0 = time.monotonic()
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if route.startswith("/api"):
            if not self._rate_ok():
                self._deny(HTTPStatus.TOO_MANY_REQUESTS, "请求过于频繁，请稍后再试")
                return
            if not self._authorized(route):
                self._deny(HTTPStatus.UNAUTHORIZED, "缺少或无效的 Bearer 令牌")
                return
            if route in LOCAL_ONLY and not is_local_ip(self.client_address[0]):
                self._deny(HTTPStatus.FORBIDDEN, "该接口仅允许本机访问")
                return

        if route.startswith("/api/v1/"):
            self._api_v1(route, params)
            return

        if route == "/api/kb":
            self._send_json(pipeline.load_kb(self.root))
            return
        if route == "/api/search":
            q = (params.get("q", [""])[0] or "").strip().lower()
            kb = pipeline.load_kb(self.root)
            if not q:
                self._send_json({"query": q, "results": []})
                return
            hits = []
            for c in kb["concepts"]:
                haystack = " ".join([c["term"], c.get("en") or "",
                                     " ".join(c.get("aliases") or []), c["definition"]]).lower()
                if q in haystack:
                    hits.append({
                        "term": c["term"], "slug": c["slug"], "category": c["category"],
                        "short_definition": c["short_definition"],
                    })
            self._send_json({"query": q, "count": len(hits), "results": hits[:20]})
            return

        dist = self.root / "dist"
        rel = route.lstrip("/") or "index.html"
        target = (dist / rel).resolve()
        if not str(target).startswith(str(dist.resolve())):
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if target.is_dir():
            target = target / "index.html"
        if not target.exists() and not Path(target).suffix:
            target = Path(str(target) + ".html")
        self._send_file(target)

    def _tele(self, payload: dict, action: str, query: str = "", result_type: str = "",
              status: int = HTTPStatus.OK) -> None:
        telemetry.for_root(self.root).record(
            "http", action, query, result_type or payload.get("type", ""), True,
            detail={"client": self._client_label(), "ip": self.client_address[0]},
        )
        self._send_json(payload, status)

    def _api_v1(self, route: str, params: dict) -> None:
        kb = knowledge.load(self.root)

        def first(name: str, default: str = "") -> str:
            return (params.get(name, [default])[0] or default).strip()

        if route == "/api/v1/health":
            stats = kb.meta.get("stats", {})
            payload = {
                "ok": True, "name": "mcai-knowledge", "version": "0.1.0",
                "built_at": kb.meta.get("built_at"),
                "concepts": stats.get("concepts"), "faqs": stats.get("faqs"),
                "relations": stats.get("relations"), "evidence": stats.get("evidence"),
                "campaign_faqs": stats.get("campaign_faqs", 0),
                "auth_required": bool(self.token),
            }
            self._tele(payload, "health")
            return
        if route == "/api/v1/catalog":
            self._tele(kb.catalog(first("category") or None), "catalog")
            return
        if route == "/api/v1/search":
            q = first("q") or first("query")
            try:
                limit = int(first("limit", "8"))
            except ValueError:
                limit = 8
            results = kb.search(q, limit=limit, category=first("category") or None)
            self._tele({"query": q, "count": len(results), "results": results}, "search", q)
            return
        if route.startswith("/api/v1/concept/"):
            key = route.rsplit("/", 1)[-1]
            concept = kb.by_slug.get(key) or kb.resolve(key)
            if not concept:
                self._tele({"ok": False, "error": f"未找到概念：{key}"}, "concept", key,
                           status=HTTPStatus.NOT_FOUND)
                return
            self._tele({"ok": True, "concept": concept}, "concept", key)
            return
        if route == "/api/v1/answer":
            q = first("q") or first("question")
            result = kb.answer(q)
            fmt = first("format", "json").lower()
            if fmt in ("md", "markdown"):
                payload = {"ok": True, "format": "markdown", "type": result.get("type"),
                           "markdown": knowledge.answer_markdown(result)}
            elif fmt == "text":
                payload = {"ok": True, "format": "text", "type": result.get("type"),
                           "text": result.get("answer", "")}
            elif fmt in ("citations", "cite"):
                payload = {"ok": True, "format": "citations", "type": result.get("type"),
                           "citations": result.get("citations", [])}
            else:
                payload = result
            self._tele(payload, "answer", q)
            return
        if route == "/api/v1/stats":
            self._tele(telemetry.for_root(self.root).stats(), "stats")
            return
        if route == "/api/v1/gaps":
            self._tele({"gaps": telemetry.for_root(self.root).gaps()}, "gaps")
            return
        if route == "/api/v1/related":
            try:
                depth = int(first("depth", "1"))
            except ValueError:
                depth = 1
            term = first("term")
            result = kb.related(term, depth=depth)
            self._tele(result, "related", term,
                       status=HTTPStatus.OK if result.get("ok") else HTTPStatus.NOT_FOUND)
            return
        self._send_json({"ok": False, "error": f"未知接口：{route}"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        self._t0 = time.monotonic()
        route = urllib.parse.urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""

        if not self._rate_ok():
            self._deny(HTTPStatus.TOO_MANY_REQUESTS, "请求过于频繁，请稍后再试")
            return
        if not self._authorized(route):
            self._deny(HTTPStatus.UNAUTHORIZED, "缺少或无效的 Bearer 令牌")
            return
        if route in LOCAL_ONLY and not is_local_ip(self.client_address[0]):
            self._deny(HTTPStatus.FORBIDDEN, "该接口仅允许本机访问")
            return

        if route == "/api/v1/answer":
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                self._send_json({"ok": False, "error": "请求体必须是 JSON"}, HTTPStatus.BAD_REQUEST)
                return
            question = (payload.get("question") or payload.get("q") or "").strip()
            if not question:
                self._send_json({"ok": False, "error": "缺少 question 字段"}, HTTPStatus.BAD_REQUEST)
                return
            self._tele(knowledge.load(self.root).answer(question), "answer", question)
            return

        if route == "/api/v1/answer/batch":
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                self._send_json({"ok": False, "error": "请求体必须是 JSON"}, HTTPStatus.BAD_REQUEST)
                return
            questions = payload.get("questions") or []
            if not isinstance(questions, list) or not questions:
                self._send_json({"ok": False, "error": "questions 必须是非空数组"}, HTTPStatus.BAD_REQUEST)
                return
            if len(questions) > 20:
                self._send_json({"ok": False, "error": "单次最多 20 个问题"}, HTTPStatus.BAD_REQUEST)
                return
            kb = knowledge.load(self.root)
            results = [kb.answer(str(q)) for q in questions]
            telemetry.for_root(self.root).record(
                "http", "answer_batch", f"{len(questions)} questions",
                detail={
                    "count": len(results),
                    "types": [r.get("type", "") for r in results],
                    "client": self._client_label(),
                },
            )
            self._send_json({"ok": True, "count": len(results), "results": results})
            return

        if route != "/api/rebuild":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self.lock.acquire(blocking=False):
            self._send_json({"ok": False, "error": "已有构建任务在进行"}, HTTPStatus.CONFLICT)
            return
        try:
            self._send_json(pipeline.rebuild(self.root))
        except Exception as exc:  # noqa: BLE001 - 回传给前端展示
            self._send_json({"ok": False, "error": f"{type(exc).__name__}: {exc}"},
                            HTTPStatus.INTERNAL_SERVER_ERROR)
        finally:
            self.lock.release()


def serve(root: str | Path, port: int = 8787, host: str = "127.0.0.1",
          token: str = "", rate_limit: int = 60, cors_origin: str = "*",
          autopilot_interval: int = 0) -> None:
    root = Path(root).resolve()
    if not (root / "dist" / "index.html").exists():
        pipeline.rebuild(root)

    handler = type("BoundHandler", (Handler,), {
        "root": root,
        "token": token or "",
        "limiter": RateLimiter(rate_limit),
        "cors_origin": cors_origin,
    })

    try:
        httpd = ThreadingHTTPServer((host, port), handler)
    except OSError as exc:
        print(f"❌ 无法监听 {host}:{port} —— {exc}")
        print("   端口可能被占用，换一个：mcai serve --port 8788")
        return

    display = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    print(f"元意识知识资产引擎已启动：http://{display}:{port}")
    print(f"  监听：{host}:{port} · 限流：{rate_limit} 次/分钟 · "
          f"鉴权：{'Bearer 令牌' if token else '关闭（仅建议本机使用）'}")
    print("  本机专属接口：/api/rebuild、/api/v1/stats、/api/v1/gaps")
    if host not in ("127.0.0.1", "::1", "localhost") and not token:
        print("⚠️  正在对外监听但没有设置令牌，任何能访问该端口的人都能查询。")
        print("   建议：mcai serve --host 0.0.0.0 --token <你的令牌>")
    if autopilot_interval > 0:
        from .autopilot import Autopilot

        pilot = Autopilot(root, port=port, ensure_server=False)

        def _loop() -> None:
            while True:
                try:
                    outcome = pilot.run_once()
                    s = outcome["status"]
                    if outcome["rebuilt"]:
                        print(f"[autopilot] 语料有变化，已重建：{s['concepts']} 概念 / {s['faqs']} 问答")
                except Exception as exc:  # noqa: BLE001
                    print(f"[autopilot] 异常：{type(exc).__name__}: {exc}")
                time.sleep(max(30, autopilot_interval))

        threading.Thread(target=_loop, name="mcai-autopilot", daemon=True).start()
        print(f"  自动驾驶：每 {autopilot_interval} 秒检查语料并自检（日志 data/autopilot.jsonl）")

    print("按 Ctrl+C 停止。")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        httpd.server_close()
