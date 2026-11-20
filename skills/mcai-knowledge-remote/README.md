# mcai-knowledge-remote

「元意识学说」知识库的**远程技能包**：不依赖本机服务，直接调用公网 API，拿回带出处的定义与问答。

适用于任何能执行 shell 命令的 Agent：豆包、Claude Code、Cursor、Windsurf、Cline、自建 Agent 等。

## 特点

- 无需本机服务、无需 API Key；
- 只读，不写入；
- 返回定义、上下文、出处；
- POSIX 与 Windows 双脚本；
- Python 标准库，无第三方依赖。

## 目录

```
mcai-knowledge-remote/
  SKILL.md              # 技能说明（Agent 读取）
  bin/
    mcai_client.py      # Python 核心（推荐）
    query.sh            # POSIX 包装
    query.ps1           # Windows PowerShell 包装
  README.md
```

## 依赖

- 首选：Python 3.7+；
- POSIX 无 Python：`curl` + `jq`，仅支持 `answer`；
- Windows 无 Python：`curl.exe`（Windows 10+），仅支持 `answer`；
- 网络：能访问公网 HTTPS。

## 测试

```sh
sh bin/query.sh answer "什么是元识？"
sh bin/query.sh batch "什么是元识|什么是元知"
sh bin/query.sh search "序生" --limit 5
sh bin/query.sh concept "元识"
sh bin/query.sh related "元识"
```

Windows：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "bin\query.ps1" answer "什么是元识？"
```

## 安装到豆包（Windows）

把整个 `mcai-knowledge-remote` 文件夹复制到：

```
%LOCALAPPDATA%\Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills\
```

然后完全退出豆包、重新打开，在「工作」模式里确认技能出现。

如果豆包账号会同步用户技能，手机端也可能读到；否则手机端需要平台支持，或改用远程 MCP。

## 安装到其他 Agent

- 能执行命令的 Agent：把本目录加入其技能/工具目录，按 `SKILL.md` 调用；
- 支持 MCP 的客户端：优先直接用远程 MCP，见 `https://mcai-knowledge-d7gtizltz910e2269-1316838521.tcloudbaseapp.com/.well-known/mcp.json`。

## 配置

环境变量：

| 变量 | 默认 | 说明 |
|---|---|---|
| `MCAI_BASE_URL` | 公网 API | 覆盖接口地址 |
| `MCAI_TIMEOUT` | `90` | 超时秒数；冷启动可能较慢 |

## 接口

| 命令 | 接口 |
|---|---|
| `answer` | `POST /api/v1/answer` |
| `batch` | `POST /api/v1/answer/batch` |
| `search` | `GET /api/v1/search?q=` |
| `concept` | `GET /api/v1/concept/{slug}` |
| `related` | `GET /api/v1/related?term=` |

## 常见问题

**返回 503 / 超时**：云托管冷启动，重试一次；默认超时 90 秒。

**返回 `type=none`**：知识库未涉及，换更具体的问法，或用 `did_you_mean`。

**Windows PowerShell 报 TLS 错误**：优先安装 Python 3，脚本会自动走 Python；否则确认 `curl.exe` 可用。

## 许可

- 代码：MIT；
- 内容：CC BY-NC-SA 4.0。
