# 发布 MCP 包（PyPI + 官方注册表）

## 当前进度

| 项目 | 状态 |
|---|---|
| wheel 包 | ✅ 已生成 `dist_pkg/mcai_knowledge-0.1.0-py3-none-any.whl`（约 100 KB） |
| 离线校验 | ✅ 解压后 `import mcai` 正常、版本元数据正常、MCP `initialize` 握手正常 |
| pip 安装校验 | ⚠️ 当前沙箱禁止 pip 写临时目录，未能在本机完成；需在正常环境验证 |
| `server.json` | ✅ 模板已放在项目根目录，需替换 `YOURNAME` |
| 发布 | ✅ 已完成：<https://pypi.org/project/mcai-knowledge/0.1.0/> |

---

## 0. 一键发布（推荐）

| 入口 | 作用 |
|---|---|
| `发布到TestPyPI.cmd` | 先演练，不影响正式包 |
| `发布到PyPI.cmd` | 正式发布 |

两个脚本都会：构建 wheel → 检查/安装 twine → 提示粘贴 API Token → 上传 → 打印验证命令。

也可以命令行执行：

```powershell
.\deploy\publish-pypi.ps1 -TestPyPI
.\deploy\publish-pypi.ps1
```

**包名可用性**：2026-10-29 查询，`mcai-knowledge` 在 PyPI 上**未被占用**。

## 1. 本地验证（在你自己电脑上）

```powershell
# 安装
python -m pip install dist_pkg\mcai_knowledge-0.1.0-py3-none-any.whl

# 建一个示例项目并构建
mcai init demo
mcai build --home demo

# 启动 MCP（stdio）
mcai-mcp --home demo
```

在 Claude Desktop / Cursor 的 MCP 配置里加：

```json
{
  "mcpServers": {
    "mcai": {
      "command": "mcai-mcp",
      "env": { "MCAI_HOME": "C:\\path\\to\\demo" }
    }
  }
}
```

（`MCAI_HOME` 也可以不写，默认取当前目录或自动探测 `config/corpus.json`。）

## 2. 发布到 PyPI

1. 注册 <https://pypi.org>，开启 2FA；
2. 生成 API Token（Account settings → API tokens）；
3. 上传：

```powershell
python -m pip install --user twine
python -m twine upload dist_pkg\mcai_knowledge-0.1.0-py3-none-any.whl
# 用户名填 __token__，密码填 pypi-xxxx
```

之后任何人可以：

```powershell
pip install mcai-knowledge
# 或
uvx --from mcai-knowledge mcai-mcp --home <项目目录>
```

## 3. 发布到 MCP 官方注册表

1. 把 `server.json` 里的 `YOURNAME` 换成 GitHub 账号；
2. 在 GitHub 建仓库并推送；
3. 安装发布工具（以官方文档为准）：

```bash
npm install -g @modelcontextprotocol/publisher
mcp-publisher validate server.json
mcp-publisher publish
```

4. 校验与认证要求见：
   - <https://modelcontextprotocol.io/registry/authentication>
   - <https://modelcontextprotocol.io/registry/remote-servers>

> 注册表对 `name`、`repository`、版本一致性有校验，`package_arguments` / `runtime_hint` 需与真实启动方式一致。
> 当前 `server.json` 采用 `uvx` + `MCAI_HOME` 的形态，发布前请用 `mcp-publisher validate` 实测。

## 4. 提交到第三方目录

- Smithery
- Glama
- mcp.so
- awesome-mcp-servers（GitHub PR）

以各站实际收录规则为准；一般需要：GitHub 仓库、可安装命令、简短说明、示例。

## 5. 版本升级流程

```powershell
# 1. 改 pyproject.toml 的 version
# 2. 重新打包（脚本自动读版本号）
python tools\build_wheel.py
# 3. 上传
python -m twine upload dist_pkg\mcai_knowledge-<新版本>-py3-none-any.whl
# 4. 更新 server.json 的 version 并重新 publish
```

## 6. 许可（已拆分）

| 对象 | 许可 | 文件 |
|---|---|---|
| 代码（`mcai/`、构建脚本、测试） | MIT | `LICENSE` |
| 知识内容（语料、定义、问答、关系、引文、数据集、站点） | CC BY-NC-SA 4.0 | `LICENSE-CONTENT` |

商业使用需另行授权。

wheel 的 METADATA 已写 `License: MIT`，并包含两份许可文件（`dist-info/licenses/`）。

## 7. 安全

- MCP 走 stdio，本地进程，不开放网络端口；
- 只读，不修改语料；
- 不包含任何 API 密钥；
- `data/`、`backups/` 不应打进包（当前 wheel 只含 `mcai/`）。
