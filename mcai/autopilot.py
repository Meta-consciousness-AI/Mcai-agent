"""自动驾驶：让知识库在无人参与下保持「活着、准着、可被调用」。

一轮循环做四件事：
1. 检查语料/配置指纹，变了就重建；
2. 记录变更日志（新增/删除/改写的术语），让每次变化可追溯；
3. 健康自检（知识库、站点、服务端口、接口响应）；
4. 把状态写到 dist/status.json 与 data/status.json，供调用方判断是否健康。

设计为「一次性执行」：由系统计划任务每 5 分钟调用一次，比常驻进程更抗崩溃。
"""
from __future__ import annotations

import hashlib
import json
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from . import dashboard, knowledge, pipeline, quality, selftest, snapshot

DEFAULT_PORT = 8787


class Autopilot:
    def __init__(self, root: str | Path, port: int = DEFAULT_PORT, ensure_server: bool = True):
        self.root = Path(root).resolve()
        self.port = port
        self.ensure_server = ensure_server
        self.data = self.root / "data"
        self.data.mkdir(parents=True, exist_ok=True)

    # ---------- 指纹 ----------
    def fingerprint(self) -> str:
        h = hashlib.sha256()
        cfg_path = self.root / "config" / "corpus.json"
        for path in sorted((self.root / "config").glob("*.json")):
            h.update(path.name.encode("utf-8"))
            h.update(path.read_bytes())
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
        except Exception:  # noqa: BLE001
            cfg = {}
        for spec in cfg.get("corpus", []):
            raw = Path(spec.get("path", ""))
            path = raw if raw.is_absolute() else self.root / raw
            if path.exists():
                stat = path.stat()
                h.update(f"{spec.get('id')}:{stat.st_size}:{int(stat.st_mtime)}".encode("utf-8"))
            else:
                h.update(f"{spec.get('id')}:missing".encode("utf-8"))
        return h.hexdigest()

    # ---------- 快照与差异 ----------
    def _snapshot(self) -> dict:
        path = self.data / "kb.json"
        if not path.exists():
            return {}
        try:
            kb = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return {
            c["term"]: hashlib.md5(c.get("definition", "").encode("utf-8")).hexdigest()
            for c in kb.get("concepts", [])
        }

    @staticmethod
    def _diff(before: dict, after: dict) -> dict:
        added = sorted(set(after) - set(before))
        removed = sorted(set(before) - set(after))
        changed = sorted(t for t in set(before) & set(after) if before[t] != after[t])
        return {"added": added, "removed": removed, "changed": changed}

    # ---------- 服务检查 ----------
    def _port_open(self) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=0.6):
                return True
        except OSError:
            return False

    def _server_healthy(self) -> bool:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/api/v1/health", timeout=2) as resp:
                return resp.status == 200
        except Exception:  # noqa: BLE001
            return False

    def _start_server(self) -> bool:
        if not self.ensure_server or self._port_open():
            return False
        flags = 0
        if sys.platform == "win32":
            flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        try:
            subprocess.Popen(
                [sys.executable, "-m", "mcai", "serve", "--home", str(self.root), "--port", str(self.port)],
                cwd=str(self.root),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags,
            )
            for _ in range(10):
                time.sleep(0.3)
                if self._port_open():
                    return True
        except Exception:  # noqa: BLE001
            return False
        return False

    # ---------- 主循环 ----------
    def run_once(self) -> dict:
        started = time.time()
        state_path = self.data / "autopilot-state.json"
        state = {}
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                state = {}

        before = self._snapshot()
        fingerprint = self.fingerprint()
        rebuilt = False
        error = ""
        result = {}

        needs_build = (fingerprint != state.get("fingerprint")) or not (self.data / "kb.json").exists()
        if needs_build:
            try:
                result = pipeline.rebuild(self.root)
                rebuilt = True
            except Exception as exc:  # noqa: BLE001
                error = f"{type(exc).__name__}: {exc}"

        after = self._snapshot()
        diff = self._diff(before, after) if rebuilt else {"added": [], "removed": [], "changed": []}

        started_server = self._start_server()
        server_ok = self._server_healthy()

        kb = {}
        try:
            kb = knowledge.load(self.root).meta.get("stats", {})
        except Exception:  # noqa: BLE001
            pass

        try:
            q = quality.inspect(self.root)
        except Exception as exc:  # noqa: BLE001
            q = {"ok": False, "counts": {"error": 1, "warn": 0},
                 "errors": [{"detail": f"{type(exc).__name__}: {exc}"}]}
        try:
            t = selftest.run(self.root)
        except Exception as exc:  # noqa: BLE001
            t = {"ok": False, "passed": 0, "total": 0, "failed": [f"{type(exc).__name__}: {exc}"]}

        now = datetime.now().astimezone().isoformat(timespec="seconds")
        status = {
            "ok": (not error and bool(kb) and (server_ok if self.ensure_server else True)
                   and q.get("ok", False) and t.get("ok", False)),
            "quality": {"ok": q.get("ok"), "errors": q.get("counts", {}).get("error", 0),
                        "warnings": q.get("counts", {}).get("warn", 0)},
            "selftest": {"ok": t.get("ok"), "passed": t.get("passed"), "total": t.get("total"),
                         "failed": t.get("failed", [])},
            "checked_at": now,
            "built_at": result.get("built_at") or kb.get("built_at"),
            "rebuilt": rebuilt,
            "started_server": started_server,
            "server_ok": server_ok,
            "concepts": kb.get("concepts"),
            "faqs": kb.get("faqs"),
            "relations": kb.get("relations"),
            "evidence": kb.get("evidence"),
            "error": error,
            "duration_ms": int((time.time() - started) * 1000),
        }

        # 写状态：data 里永久保留，dist 里给外部读（重建会清空 dist，所以最后写）
        (self.data / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        dist = self.root / "dist"
        if dist.exists():
            (dist / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

        # 变更日志
        if rebuilt and before and (diff["added"] or diff["removed"] or diff["changed"]):
            entry = {"ts": now, **diff, "concepts": status["concepts"], "faqs": status["faqs"]}
            with (self.data / "changelog.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

        with (self.data / "autopilot.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(status, ensure_ascii=False) + "\n")

        try:
            dashboard.render(self.root)
        except Exception:  # noqa: BLE001 - 看板失败不影响巡检
            pass

        if rebuilt:
            try:
                snap = snapshot.create(self.root, note="自动快照：语料变更", keep=8)
                status["snapshot"] = Path(snap["archive"]).name
            except Exception:  # noqa: BLE001 - 快照失败不影响巡检
                pass
            state["fingerprint"] = fingerprint
            state["last_build"] = now
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

        return {"status": status, "diff": diff, "rebuilt": rebuilt}

    def loop(self, interval: int = 60) -> None:
        print(f"自动驾驶已启动（每 {interval} 秒检查一次，Ctrl+C 停止）")
        while True:
            try:
                outcome = self.run_once()
                s = outcome["status"]
                flag = "重建" if outcome["rebuilt"] else "无变化"
                print(f"[{s['checked_at']}] {flag} · {s['concepts']} 概念 · 服务 "
                      f"{'在线' if s['server_ok'] else '离线'} · {s['duration_ms']}ms")
            except KeyboardInterrupt:
                raise
            except Exception as exc:  # noqa: BLE001
                print(f"[{datetime.now().isoformat(timespec='seconds')}] 异常：{type(exc).__name__}: {exc}")
            time.sleep(max(5, interval))
