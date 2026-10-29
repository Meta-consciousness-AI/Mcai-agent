# mcai-knowledge 0.2.0

命名统一版本：全项目改用 **mcai**（Meta-consciousness-AI）。

## 重要变更

- PyPI 包名：`mca-knowledge` → **`mcai-knowledge`**
- 命令行：`mca` → **`mcai`**，`mca-mcp` → **`mcai-mcp`**
- Python 模块：`mca` → **`mcai`**（`import mcai`）
- 环境变量：`MCA_HOME` → **`MCAI_HOME`**，`MCA_TOKEN` → **`MCAI_TOKEN`**
- MCP 服务器名：**`mcai-knowledge`**
- 资源 URI：`mca://` → **`mcai://`**
- 仓库：<https://github.com/Meta-consciousness-AI/mcai-agent>

旧包 `mca-knowledge` 0.1.0 将标记为废弃（yank），请改用新包。

## 安装

```bash
pip install mcai-knowledge
```

MCP：

```bash
mcai-mcp --home <项目目录>
```

Claude Desktop / Cursor：

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

## 兼容说明

0.1.0 没有外部用户，因此不做旧命令别名；如已安装旧包，请先卸载：

```bash
pip uninstall mca-knowledge
pip install mcai-knowledge
```

## 许可

- 代码：MIT
- 知识内容：CC BY-NC-SA 4.0
