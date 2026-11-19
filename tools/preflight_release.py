# -*- coding: utf-8 -*-
"""发布前自检：版本一致性、Docker 构建上下文、包内知识库。

用法：
    python tools/preflight_release.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []
warnings: list[str] = []


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    ).stdout.strip()


def main() -> int:
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    print("版本：", version)

    # 1. 版本一致性
    checks = {}
    cfg = json.loads((ROOT / "config" / "corpus.json").read_text(encoding="utf-8"))
    checks["config/corpus.json"] = cfg["project"].get("version")
    kb = json.loads((ROOT / "data" / "kb.json").read_text(encoding="utf-8"))
    checks["data/kb.json"] = kb["meta"]["project"].get("version")
    pkg = json.loads((ROOT / "mcai" / "data" / "default" / "data" / "kb.json").read_text(encoding="utf-8"))
    checks["mcai/data/default/data/kb.json"] = pkg["meta"]["project"].get("version")
    init = (ROOT / "mcai" / "__init__.py").read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"([^"]+)"', init)
    checks["mcai/__init__.py"] = m.group(1) if m else None
    sj = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    checks["server.json"] = sj.get("version")

    for name, v in checks.items():
        if v != version:
            errors.append(f"版本不一致：{name} = {v}，应为 {version}")

    # 2. Dockerfile 的 COPY 源必须存在且未被 gitignore
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    for line in dockerfile.splitlines():
        line = line.strip()
        if not line.upper().startswith("COPY "):
            continue
        parts = line.split()
        for src in parts[1:-1]:
            if src.startswith("--"):
                continue
            p = ROOT / src
            if not p.exists():
                errors.append(f"Dockerfile COPY 源不存在：{src}")
                continue
            ignored = git("check-ignore", "-q", src)
            if ignored:
                # check-ignore 成功返回路径
                errors.append(f"Dockerfile COPY 源被 gitignore 排除：{src}")

    # 3. 包内知识库必须被跟踪
    tracked = git("ls-files", "mcai/data/default/data/kb.json")
    if not tracked:
        errors.append("包内知识库未被 git 跟踪：mcai/data/default/data/kb.json")

    # 4. 静态站点是否已按当前版本重建
    index = ROOT / "dist" / "index.html"
    if not index.exists():
        warnings.append("dist/index.html 不存在：发布前需运行 tools/build_site_from_kb.py")
    else:
        html = index.read_text(encoding="utf-8", errors="replace")
        if f"v{version}" not in html:
            warnings.append(f"dist/index.html 未包含 v{version}：站点可能未重建")

    # 5. 当前分支与远程提示
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    print("当前分支：", branch)
    if branch != "main":
        warnings.append("当前不在 main 分支")

    print("\n结果：")
    for w in warnings:
        print("  警告：", w)
    for e in errors:
        print("  错误：", e)
    if errors:
        print("\n发布前自检未通过")
        return 1
    print("\n发布前自检通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
