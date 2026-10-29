"""DeepSeek API 客户端（标准库实现，无第三方依赖）。

密钥从 config/llm.json 指向的文件读取，也可用环境变量 DEEPSEEK_API_KEY 覆盖。
密钥不会被写进任何产物或日志。
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"


class LLMError(RuntimeError):
    pass


class LLM:
    def __init__(self, config_path: str | Path | None = None):
        cfg: dict = {}
        if config_path:
            p = Path(config_path)
            if p.exists():
                cfg = json.loads(p.read_text(encoding="utf-8-sig"))
        self.base_url = (cfg.get("base_url") or DEFAULT_BASE).rstrip("/")
        self.model = cfg.get("model") or DEFAULT_MODEL
        self.timeout = int(cfg.get("timeout", 60))
        self.retries = int(cfg.get("retries", 2))
        self.key = os.environ.get("DEEPSEEK_API_KEY") or self._read_key(cfg.get("key_path"))
        self.calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    @staticmethod
    def _read_key(path: str | None) -> str:
        if not path:
            return ""
        p = Path(path)
        return p.read_text(encoding="utf-8-sig").strip() if p.exists() else ""

    @property
    def available(self) -> bool:
        return bool(self.key)

    def chat(self, messages: list[dict], temperature: float = 0.0,
             max_tokens: int = 700) -> str:
        if not self.available:
            raise LLMError("未找到 API 密钥：请检查 config/llm.json 的 key_path 或环境变量 DEEPSEEK_API_KEY")
        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }, ensure_ascii=False).encode("utf-8")

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.key}",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                usage = data.get("usage") or {}
                self.calls += 1
                self.prompt_tokens += int(usage.get("prompt_tokens") or 0)
                self.completion_tokens += int(usage.get("completion_tokens") or 0)
                return (data["choices"][0]["message"]["content"] or "").strip()
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", "replace")[:300]
                last_error = LLMError(f"HTTP {exc.code}: {body}")
                if exc.code in (400, 401, 403, 404):
                    break
            except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
                last_error = LLMError(f"{type(exc).__name__}: {exc}")
            if attempt < self.retries:
                time.sleep(1.5 * (attempt + 1))
        raise last_error or LLMError("调用失败")

    def stats(self) -> dict:
        return {
            "model": self.model,
            "calls": self.calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
        }
