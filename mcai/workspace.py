"""工作区解析与初始化。

代码在包里，数据在工作区里：
- MCAI_HOME 环境变量 → 优先；
- 当前目录有 config/corpus.json → 用它；
- 否则回退到开发目录（源码仓库根），最后才是当前目录。
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parent
DEV_ROOT = PKG_ROOT.parent
TEMPLATES = PKG_ROOT / "templates"

README_TEMPLATE = """# 元意识知识库工作区

这个目录只放你的数据，代码在安装的包里（`pip install -e .` 或 `pip install mcai-knowledge`）。

## 结构

```
config/
  corpus.json           语料清单（把 docx/pdf 路径填进来）
  curated.json          编辑层：别名、英文名、核心关系、种子问答
  disambiguation.json   阶段性消歧（可整体关闭）
  overrides.json        人工裁定层（优先级最高）
  llm.json              抽检/内容工厂用的模型配置（可选）
corpus/                 把要接入的文档放这里
data/                   构建产物（kb.json、usage.jsonl）
dist/                   静态站与数据集
```

## 三步开始

1. 把文档放进 `corpus/`，在 `config/corpus.json` 里登记路径与类型：
   - `glossary`：提供定义（术语表）
   - `evidence`：只提供引文与出处
   - `playbook`：仅作语境，不参与抽取
2. `mcai build`
3. `mcai serve` 或 `mcai mcp`

## 常用命令

```bash
mcai build                 # 重建知识库、站点、数据集
mcai serve --port 8787     # 本地网页 + HTTP API
mcai mcp                   # MCP 服务器（stdio）
mcai report                # 体检：冲突、覆盖、分类
mcai disambig              # 阶段性消歧状态
mcai stats                 # 调用统计
mcai gaps                  # 未命中的问题（人工补词输入）
```
"""


def resolve_home(explicit: str | None = None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env = os.environ.get("MCAI_HOME")
    if env:
        candidates.append(Path(env).expanduser())
    candidates.append(Path.cwd())
    candidates.append(Path(__file__).resolve().parent / "data" / "demo")
    candidates.append(DEV_ROOT)
    for cand in candidates:
        if (cand / "config" / "corpus.json").exists():
            return cand.resolve()
    return Path.cwd().resolve()


def init_workspace(target: str | Path, force: bool = False) -> dict:
    root = Path(target).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    for sub in ("config", "corpus", "data"):
        (root / sub).mkdir(exist_ok=True)

    created: list[str] = []
    skipped: list[str] = []
    src_dir = TEMPLATES / "config"
    if src_dir.exists():
        for src in sorted(src_dir.glob("*.json")):
            dst = root / "config" / src.name
            if dst.exists() and not force:
                skipped.append(str(dst))
                continue
            shutil.copyfile(src, dst)
            created.append(str(dst))

    readme = root / "README.md"
    if not readme.exists() or force:
        readme.write_text(README_TEMPLATE, encoding="utf-8")
        created.append(str(readme))

    return {"root": str(root), "created": created, "skipped": skipped}
