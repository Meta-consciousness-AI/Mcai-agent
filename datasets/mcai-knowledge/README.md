---
license: cc-by-nc-sa-4.0
language:
- zh
pretty_name: 元意识学说知识库
task_categories:
- question-answering
- text-generation
tags:
- knowledge-base
- mcp
- terminology
- meta-consciousness
---

# 元意识学说知识库（MCAI Knowledge Base）

元意识学说的结构化知识资产：术语定义、标准问答、原文引证、概念关系与训练数据。

- **概念**：64 个术语（含 6 个衍生术语），每个定义带原文出处
- **问答**：122 组标准问答（定义、辨析、引证、阶段性消歧）
- **关系**：270 条概念关系（含核心闭环与「提及」关系）
- **引证**：213 条文献原句

## 文件

| 文件 | 说明 |
|---|---|
| `concepts.jsonl` | 概念词条（定义、别名、英文、出处、引证、关系） |
| `faq.jsonl` | 标准问答 |
| `evidence.jsonl` | 文献引证原句 |
| `sft.jsonl` | 指令微调格式（question / answer / sources） |
| `concepts.csv` | 概念表（便于表格工具查看） |
| `knowledge-graph.json` | 概念关系图（节点 + 边） |

每行一个 JSON 对象，UTF-8 编码。

## 用途

- RAG 检索与知识库构建
- 术语一致性校验
- 概念关系抽取与图谱补全
- 指令微调 / 评测数据

## 许可

知识内容采用 **CC BY-NC-SA 4.0**：署名、非商业、相同方式共享。
商业使用需另行授权。

## 相关

- 站点：https://mcai-knowledge-d7gtizltz910e2269-1316838521.tcloudbaseapp.com
- DOI：https://doi.org/10.5281/zenodo.23789330
- MCP 包：https://pypi.org/project/mcai-knowledge/
- 代码：https://github.com/Meta-consciousness-AI/Mcai-agent
