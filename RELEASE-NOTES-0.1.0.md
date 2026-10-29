# mcai-knowledge 0.1.0

把一套学说做成 AI / Agent 能直接调用的结构化知识资产。

这是首个公开版本，已发布到 PyPI：<https://pypi.org/project/mcai-knowledge/0.1.0/>

## 安装

```bash
pip install mcai-knowledge
```

或直接通过 uv 运行 MCP：

```bash
uvx --from mcai-knowledge mcai-mcp --home <项目目录>
```

## 快速开始

```bash
mcai init demo
# 把 Word/PDF 放进 demo/corpus/，修改 demo/config/corpus.json
mcai build --home demo
mcai serve --home demo --port 8787
```

MCP（stdio）：

```bash
mcai-mcp --home demo
```

Claude Desktop / Cursor 配置：

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

## 这个版本包含

- **结构化词条**：术语定义、别名、关系、原文引证；
- **标准问答**：定义类、对比类、引证类；
- **站点**：每概念独立 URL、Schema.org（DefinedTerm / FAQPage / Dataset）、llms.txt、sitemap；
- **数据集**：concepts / faq / evidence / sft / graph，JSONL + CSV；
- **接口**：HTTP API（`/api/v1/*`）与 MCP（stdio，5 个工具 + 指南资源）。

内置示例知识库：64 个概念、122 组问答、270 条关系。

## 许可

- 代码：MIT（`LICENSE`）
- 知识内容：CC BY-NC-SA 4.0（`LICENSE-CONTENT`）
- 商业使用需另行授权

## 链接

- PyPI：<https://pypi.org/project/mcai-knowledge/>
- 文档：仓库内 `docs/`
- 问题反馈：仓库 Issues
