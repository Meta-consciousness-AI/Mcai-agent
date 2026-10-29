# 交接与恢复指南

> 这份文件是给「停一段时间后再回来」用的。即使换了新的对话、换了模型，读这一页就能接上。

最后更新：2026-10-18

---

## 一句话现状

元意识知识库已建成并可被本机 AI/Agent 调用：64 个概念、122 组问答、267 条关系、213 条引文；
质量巡检 0 错 0 警，接口自检 12/12；服务带自动驾驶，启动后自动维护。

唯一目标是**被其他 AI / Agent 调用**，不做人类传播、不自动生成问答。

---

## 恢复只需三步

1. 双击项目根目录的 **`启动.cmd`**（后台启动；想看得见就双击 `start.bat`）
2. 浏览器打开 <http://127.0.0.1:8787>
3. 想看健康状态：`python -m mcai status`，或打开 <http://127.0.0.1:8787/dashboard.html>

停止：双击 **`停止.cmd`**，或关掉 `start.bat` 的窗口。

---

## 关键路径

| 内容 | 位置 |
|---|---|
| 项目根目录 | `C:\Users\HP\Documents\deepseek-harness\default-workspace\mcai-agent` |
| 语料（Word/PDF） | `E:\th\元意识\元意识运营\`（路径写在 `config/corpus.json`） |
| 知识库主数据 | `data/kb.json` |
| 调用日志 / 状态 / 质量 / 变更 | `data/usage.jsonl`、`status.json`、`quality.json`、`selftest.json`、`changelog.jsonl` |
| 站点与数据集 | `dist/`（`dist/dataset/` 下是导出文件） |
| 配置 | `config/corpus.json`、`curated.json`、`disambiguation.json`、`overrides.json`、`llm.json` |
| Python（本机） | `C:\Users\HP\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe` |

---

## 当前数据快照

```
概念 64（58 主词条 + 6 衍生术语）
问答 122（核心 8 · 辨析 6 · 定义 64 · 原典 34 · 阶段性消歧 10）
关系 267 · 引证 213 · 语料 8 份 / 953 段 / 115,247 字
质量：0 错误 0 警告（11 条提示：缺英文名）
自检：12/12
```

---

## 已经做完的

- 语料解析（docx/pdf，含 Word 手动换行、章节提升、相对路径）
- 概念抽取、多源合并、冲突检测、别名归一、衍生术语
- 阶段性消歧（可一键关闭，定义永不含否定句）
- Schema.org / JSON-LD、独立 URL 站点、llms.txt、sitemap
- 数据集导出（concepts/faq/evidence/sft/csv/知识图谱）
- HTTP API + MCP（5 工具、3 prompts、guide 资源）
- 调用遥测、缺口清单、阶段报告
- 模型抽检（baseline vs grounded）
- 内容工厂（7 种格式，可选配件，默认人工审）
- 安全暴露（令牌、限流、CORS、访问日志、本机专属接口）
- 自动驾驶（指纹检测、自动重建、变更日志、质量巡检、接口自检、状态文件、观测台）

---

## 明确暂停的（不是没做完，是等条件）

| 事项 | 卡在哪 |
|---|---|
| 开机自启 | 沙箱拒绝注册计划任务/启动目录；需在正常权限下一次性安装 |
| 公网可达 | 需要部署位置（云主机或隧道）与安全决策 |
| 被外部 Agent 调用 | 依赖上面两项 + 对方接入 |
| 提交目录 / 对接合作方 | 需要人的账号与动作 |
| 自动生成 FAQ | 已明确不做：会引入术语解读偏差 |

---

## 下次想继续时，可以选的下一步

1. 把 `data/status.json` 暴露成 LAN 内网可读（需 `--host 0.0.0.0` + 令牌）
2. 真机验证「隐藏启动」在正常 Windows 权限下是否存活
3. 补 11 个缺失的英文名（人工编辑 `config/overrides.json`）
4. 周度抽检（花少量 API 费用）
5. 重新评估是否公开部署

---

## 环境备忘

- 本机 `pip` 被沙箱限制，无法安装；用 `python -m mcai ...` 或 `run.py` 形式运行。
- 语料在 E 盘，路径失效时 `mcai build` 会报错，按提示改 `config/corpus.json`。
- `config/llm.json` 指向本地 API 密钥文件（仅用于抽检与内容工厂；已授权）。
- 服务默认 `127.0.0.1:8787`，只允许本机访问。

---

## 对话与文件的关系

- 对话记录由 DeepSeek Harness 保存在 `C:\Users\HP\.dsh\sessions\`，关客户端不会删除；
- 但**新开一个对话不会自动带着旧上下文**。所以把「状态」写进文件（本页 + README + data/status.json），
  比依赖聊天记录更可靠。

---

## 本地快照（备份与回滚）

本机没有 git，用 zip 快照代替：

```bash
mcai snapshot -m "改动说明"     # 打一份快照（含代码、配置、知识库、语料）
mcai snapshots                 # 列出已有快照
mcai restore backups\snapshot-xxxx.zip --to D:\mcai-bak   # 恢复到新目录
```

- 存放位置：`backups/`，默认保留最近 8 份（每份约 2.2 MB）
- 自动触发：自动驾驶检测到语料变化并重建时，会自动打一份
- 恢复是「解压到新目录」，不会覆盖现有文件；确认无误后再替换
---

## 里程碑

- **2026-10-19 00:28｜首次被外部 AI 应用调用**
  豆包桌面版（2.31.4，工作模式 + 本地电脑）在本机执行 PowerShell，
  请求 `/api/v1/answer` 提问「什么是元意识学说」，拿到定义与出处，并在回答中正确引用
  《元意识学说极简版（标准词表）》。
  证据：`data/access.log` 00:28:19、00:30:26 三条 `WindowsPowerShell` 记录，`type=faq`。
  意义：单机范围内的「被其他 AI 调用」已经跑通；跨机器调用仍需公网部署。

- 观测台新增「命令行调用」卡片（按客户端 UA 分类：自检 / 命令行 / 浏览器 / MCP），
  用来区分「我的脚本」与「别的 AI 通过命令行调用」。
- **2026-10-19 00:53｜技能固化生效**
  安装 `mcai-knowledge` 技能后，在豆包「工作」模式新对话里只输入「什么是元意识学说？」，
  未给任何执行指令，豆包自动调用 `/api/v1/answer` 并带出处作答。
  证据：`data/access.log` 00:53:01 的 `POST /api/v1/answer`，客户端为 WindowsPowerShell。
  意义：从「每次叮嘱」变为「一次安装、长期生效」。
---

## 收录边界（长期政策）

**只收学说，不收人。**

- 收录：术语、定义、关系、原文引文；
- 不收录：作者姓名、生平、身份、观点归属（当前排除名单：布衣祭酒）。

工程上做了强制检查，不靠自觉：

| 环节 | 行为 |
|---|---|
| 词条抽取 | 排除名单中的词不能成为概念 |
| 引证筛选 | 含人物名的句子不进引文库 |
| 问答路由 | 问人物 → 返回 `type=policy` 的统一说明；问「某人的某学说」→ 仍回答学说，并附一句「本库只收学说术语」 |
| 质量巡检 | 任何内容里出现人物名 → 记 `policy.entity_leak` 错误，构建体检不通过 |
| 观测台 | 展示层把人物名遮蔽为「（作者）」（日志本身保留，供排查） |

理由：学说与个人分离。一旦绑定到具体的人，学说的解释权与传播就会被个人因素牵连；
把它当作时代「序生」的产物，反而更长久。
- **2026-10-29｜PyPI 首发 mcai-knowledge 0.1.0**
  上传成功，PyPI 上的 wheel sha256 与本地一致（f9ddf2e7…7046f），
  元数据：License MIT、依赖 python-docx/lxml、README 长描述 14,671 字符。
  地址：https://pypi.org/project/mcai-knowledge/0.1.0/
  许可：代码 MIT，知识内容 CC BY-NC-SA 4.0。
- **2026-10-29 12:10｜mcai-knowledge 0.2.0 发布**
  统一命名（mca → mcai）后重新发布；PyPI wheel sha256 与本地一致
  （3a0b3589…ed189），License MIT，依赖 python-docx/lxml。
  GitHub：https://github.com/Meta-consciousness-AI/mcai-agent
  PyPI：https://pypi.org/project/mcai-knowledge/0.2.0/
- **2026-10-29 12:4x｜MCP 官方注册表收录**
  `io.github.Meta-consciousness-AI/mcai-knowledge` 0.2.1 已发布，status=active，
  包类型 pypi，identifier `mcai-knowledge`。
  查询：https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.Meta-consciousness-AI/mcai-knowledge
  三件套完成：PyPI 可安装、GitHub 仓库、MCP 注册表可检索。
- **2026-10-29 14:16｜Glama 收录并通过自动检查**
  构建 success（7.6s），5 个工具被识别：mcai_answer / mcai_concept / mcai_list / mcai_related / mcai_search。
  页面：https://glama.ai/mcp/servers/Meta-consciousness-AI/Mcai-agent
  说明：Glama 用仓库内 Dockerfile/配置构建，pip 不可用时改用 uv；Pinned commit 需与 GitHub 同步。
## 工作约定

- 每次回复的末尾显示「待办」清单，来源：`docs/待办.md`。
- 完成一项就更新该文件，保持「待完成 / 已暂停 / 最近完成」三段。
- 被外部条件阻塞（如 GitHub 网络）的项标 `[!]`，不要反复重试。