"""上线工具：设置站点地址、远程自检。

对外暴露前必须把 project.site_url 改成真实地址，否则 .well-known 清单里写的还是本地地址，
别的 Agent 拿到清单也接不上。doctor 就是用来发现这类不一致的。
"""
from __future__ import annotations

import json
import secrets
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def set_site_url(home: str | Path, url: str) -> dict:
    url = (url or "").strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        raise ValueError("地址必须以 http:// 或 https:// 开头")
    path = Path(home) / "config" / "corpus.json"
    cfg = json.loads(path.read_text(encoding="utf-8-sig"))
    old = (cfg.get("project") or {}).get("site_url", "")
    cfg.setdefault("project", {})["site_url"] = url
    path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"old": old, "new": url, "path": str(path)}


def new_token() -> str:
    return secrets.token_urlsafe(24)


def _get(url: str, token: str = "", timeout: int = 10) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "mcai-doctor/0.1"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except Exception as exc:  # noqa: BLE001 - 网络错误统一成状态 0
        return 0, str(exc).encode("utf-8")


def doctor(url: str, token: str = "", timeout: int = 10) -> list[dict]:
    """对已部署的实例做一轮体检，返回检查项列表。"""
    base = (url or "").strip().rstrip("/")
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str, hint: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail, "hint": hint})

    # 1. 存活
    status, body = _get(f"{base}/api/v1/health", timeout=timeout)
    health = {}
    if status == 200:
        try:
            health = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            health = {}
        add("health", True,
            f"{health.get('concepts')} 概念 / {health.get('faqs')} 问答 · "
            f"auth_required={health.get('auth_required')}")
    else:
        add("health", False, f"HTTP {status}", "服务未启动，或地址/端口不对")

    # 2. MCP 清单里的地址是否与部署地址一致
    status, body = _get(f"{base}/.well-known/mcp.json", timeout=timeout)
    if status == 200:
        try:
            manifest = json.loads(body.decode("utf-8"))
            manifest_base = (manifest.get("http") or {}).get("base", "")
        except json.JSONDecodeError:
            manifest_base = ""
        ok = manifest_base.startswith(base)
        add("manifest", ok, f"清单地址：{manifest_base or '缺失'}",
            "" if ok else "运行 mcai set-url <当前地址> 后重新 build")
    else:
        add("manifest", False, f"HTTP {status}", "尚未构建，或 .well-known 未生成")

    # 3. 接入指南（给 Agent 读的说明书）
    status, body = _get(f"{base}/llms.txt", timeout=timeout)
    add("llms.txt", status == 200, f"HTTP {status}")

    # 4. 问答是否可用
    q = urllib.parse.quote("什么是元意识")
    status, body = _get(f"{base}/api/v1/answer?q={q}", token=token, timeout=timeout)
    answer_type = ""
    if status == 200:
        try:
            answer_type = json.loads(body.decode("utf-8")).get("type", "")
        except json.JSONDecodeError:
            answer_type = ""
    ok = status == 200 and answer_type in ("concept", "faq", "relation")
    add("answer", ok, f"HTTP {status} · type={answer_type or '-'}",
        "" if ok else ("需要令牌时请加 --token" if status in (401, 403) else "检查知识库是否构建"))

    # 5. 鉴权是否真的生效
    if token:
        status_anon, _ = _get(f"{base}/api/v1/answer?q={q}", timeout=timeout)
        add("auth", status_anon in (401, 403), f"无令牌访问：HTTP {status_anon}",
            "" if status_anon in (401, 403) else "令牌未生效：检查启动参数 --token")
    else:
        add("auth", True, "未配置令牌（仅建议本机）", "对外暴露请设置 --token")

    return checks
