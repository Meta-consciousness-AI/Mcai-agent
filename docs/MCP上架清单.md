# MCP 上架清单

> 目标：让 `mcai-knowledge` 出现在 MCP 官方注册表和主流目录里，开发者能搜到、一键安装。
> 前置：PyPI 已发布 0.1.0（✅ 已完成）。

---

## 第 0 步：安装 Git

当前这台电脑**没有安装 git**，需要先装一个（任选其一）：

| 方式 | 说明 |
|---|---|
| Git for Windows | <https://git-scm.com/download/win>，下载后一路下一步 |
| winget | 管理员 PowerShell 执行 `winget install --id Git.Git` |
| GitHub Desktop | <https://desktop.github.com>，自带 git，图形界面 |

装完在 PowerShell 里执行 `git --version`，能看到版本号即可。

> 没有 git 也可以先用 GitHub 网页的 "Upload files" 上传，但文件多时很麻烦，不推荐。

## 第 1 步：确认没有敏感文件进仓库

仓库里不能有：

- `data/`（运行日志、令牌、使用记录）
- `config/corpus.json`（含本机绝对路径）
- `config/llm.json`（含密钥路径）
- `corpus/` 里的原始 Word/PDF（版权与体积）

这些已在 `.gitignore` 中排除。推送前检查：

```powershell
git status --short
```

应该只看到代码、文档、示例配置。

用户拿到仓库后这样初始化：

```powershell
copy config\corpus.example.json config\corpus.json
copy config\llm.example.json config\llm.json
# 编辑 corpus.json 里的路径，把文档放进 corpus/
```

---

## 第 2 步：建 GitHub 仓库并推送

在 GitHub 新建仓库 `mcai-agent`（Public，不要勾选初始化 README）。

```powershell
cd C:\Users\HP\Documents\deepseek-harness\default-workspace\mcai-agent
git init
git add .
git commit -m "mcai-knowledge 0.1.0"
git branch -M main
git remote add origin https://github.com/<你的用户名>/mcai-agent.git
git push -u origin main
```

> 如果 `git init` 报"已存在"，说明仓库已初始化，跳过即可。
> 推送前确认 `git status` 里没有 `data/` 和 `config/corpus.json`。

---

## 第 3 步：填 server.json

注册表要求名称格式为 `io.github.<用户名>/<服务器名>`，仓库地址也要对应。

```powershell
.\deploy\gen-server-json.ps1 -GitHubUser <你的用户名>
```

脚本会自动：

- 把 `name` 改成 `io.github.<用户名>/mcai-knowledge`；
- 把 `repository.url` 改成你的仓库地址；
- 从 `pyproject.toml` 读取版本号，同步到 `server.json`。

先预览可以加 `-DryRun`。

---

## 第 4 步：安装并运行 mcp-publisher

官方文档：<https://modelcontextprotocol.io/registry/>

安装方式（以官方为准）：

| 系统 | 方式 |
|---|---|
| macOS / Linux | `brew install mcp-publisher` |
| Windows | 从 GitHub Releases 下载 `mcp-publisher_windows_amd64.zip`，解压后把目录加入 PATH |
| 有 Go 环境 | `go install github.com/modelcontextprotocol/registry/cmd/publisher@latest` |

运行：

```bash
# 1. 校验 server.json
mcp-publisher validate server.json

# 2. 用 GitHub 登录（浏览器授权）
mcp-publisher login github

# 3. 发布
mcp-publisher publish
```

> 登录的 GitHub 账号必须与 `server.json` 里的 `io.github.<用户名>` 一致。
> 仓库必须是公开的，否则校验会失败。

---

## 第 5 步：提交第三方目录

| 目录 | 提交方式 | 需要准备 |
|---|---|---|
| Smithery | <https://smithery.ai> 连接 GitHub 仓库，或按其 CLI 发布 | 仓库、安装命令 |
| Glama | <https://glama.ai/mcp/servers> 提交仓库 URL | 仓库、简介 |
| mcp.so | <https://mcp.so> 提交表单 | 名称、描述、仓库、安装命令 |
| awesome-mcp-servers | 向 `punkpeye/awesome-mcp-servers` 提 PR | 一行条目：名称 + 链接 + 说明 |
| PulseMCP | <https://www.pulsemcp.com> 提交 | 同上 |

通用材料：

```
名称：mcai-knowledge
简介：元意识学说知识库：术语定义、概念关系与原文出处，供 AI/Agent 通过 MCP 调用
安装：pip install mcai-knowledge
运行：mcai-mcp --home <项目目录>
仓库：https://github.com/<用户名>/mcai-agent
许可：MIT（代码）/ CC BY-NC-SA 4.0（内容）
```

---

## 第 6 步：验证

1. 在注册表搜索 `mcai-knowledge`，确认条目存在；
2. 在一台干净机器上：

```powershell
pip install mcai-knowledge
mcai init demo
mcai build --home demo
mcai-mcp --home demo
```

3. 在 Claude Desktop / Cursor 里配置并试调一个工具。

---

## 常见错误

| 报错 | 原因 | 处理 |
|---|---|---|
| `name must match io.github.<user>/...` | 用户名与 GitHub 账号不符 | 用 `gen-server-json.ps1` 重新生成 |
| `repository not found` | 仓库私有或地址错 | 改成 Public，检查 URL |
| `version mismatch` | server.json 与 PyPI 版本不一致 | 改版本号后重新生成 |
| `package not found` | PyPI 上还没有对应版本 | 先发 PyPI，再上注册表 |
| `401/403` | 未登录或登录过期 | `mcp-publisher login github` 重新登录 |

---

## 以后发新版本

```powershell
# 1. 改 pyproject.toml 的 version（例如 0.1.1）
python tools\build_wheel.py
# 2. 发布 PyPI
双击 发布到PyPI.cmd
# 3. 同步 server.json
.\deploy\gen-server-json.ps1 -GitHubUser <用户名>
# 4. 重新提交注册表
mcp-publisher publish
```

PyPI 的版本号不可覆盖，每次发版必须递增。
