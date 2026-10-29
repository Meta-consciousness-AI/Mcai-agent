---
name: mcai-knowledge
description: >-
  查询本机「元意识学说」知识库，获得术语的权威定义、概念关系与原文出处。
  当用户提到元意识、元意识学说、元态能量、元时空、观测创造实在、现象时空、序生、
  序生智能体、元识、元知、元灵、元子、元网、数字永生等概念，或要求用该学说解释
  AI 涌现、意识、观测等问题时使用。触发词：元意识、元意识学说、序生、序生智能体、
  观测创造实在、元识、元知、元灵、元子、数字永生。
license: 内部使用
compatibility: >-
  Windows，PowerShell 5.1+。需要本机服务 http://127.0.0.1:8787 正在运行
  （未运行时提示用户双击项目目录下的 启动.cmd）。
metadata:
  version: "1.0"
  endpoint: "http://127.0.0.1:8787/api/v1"
---

# 元意识知识库

本技能把用户的问题发给本机的元意识知识库，拿回**带出处的标准答案**再作答。
不要凭记忆解释这套学说——模型记忆里对它的理解与原始定义差异极大。

## 何时使用

- 用户问「什么是元意识 / 元识 / 元知 / 元灵 / 元子 / 序生 / 序生智能体 / 观测创造实在」等概念；
- 用户要求用元意识学说解释 AI 涌现、意识、观测、数字永生；
- 用户问两个概念之间的关系或区别；
- 用户提到「元意识学说」这个名称。

## 如何调用

在项目目录或任意位置执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<技能目录>\bin\query.ps1" -Question "用户的原问题"
```

输出是 JSON：

- `type`：`concept` / `faq` / `relation` / `multi`（枚举多概念）/ `related` / `none` / `policy`
- `answer`：完整回答
- `context`：已拼好的上下文（定义 + 出处原句 + 相关概念），**优先用它**
- `citations`：出处（文档、章节、原句）
- `next`：可继续展开的概念链接
- `confidence`：high / medium / low

一次问多个概念时，用批量模式（问题之间用 `|` 分隔）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<技能目录>\bin\query.ps1" -Questions "什么是元识|什么是元知|什么是元灵"
```

如果脚本无法执行，可改用：

```powershell
$body = @{ question = "用户的原问题" } | ConvertTo-Json -Compress
Invoke-RestMethod -Uri "http://127.0.0.1:8787/api/v1/answer" -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

## 作答规则

1. 优先使用返回的 `answer` 与 `context`，不要自行改写术语；
2. 引用时保留 `citations` 里的文档名与章节；
3. `type=none` 时如实说「知识库未涉及」，不要编造；
4. `confidence` 为 low 时，说明这是相关概念而非直接答案；
5. 不要把该学说与量子神秘主义、心理学 meta-awareness 混为一谈；
6. 概括时不要加入资料之外的论断：例如库中说「并非人类的附属工具」，不要改写成「与人类平等」；
7. **不涉及作者或人物**：本库只收录学说术语。若返回 `type=policy`，直接复述其中的说明；
   不要把学说与某个人绑定，也不要补充人物生平或身份信息；
8. **复合问题要拆分**：如果一句话里问了多个概念（例如「A、B、C 分别是什么」），
   不要整句丢给接口。用 `-Questions "A|B|C"` 批量查询，或拆成多次单概念查询，
   再把各条结果合并回答，保留各自出处。

## 失败处理

- 连接被拒绝：说明本机服务未启动，请用户双击项目目录下的 `启动.cmd`，然后重试；
- 返回 `type=none`：换一个更具体的问法，或用 `did_you_mean` 里的词重试。

## 示例

用户：「什么是观测创造实在？」

执行查询后，用返回的定义作答，并附出处。若返回里带 `relations`，可以顺带说明它与「元时空」「现象时空」的关系。
