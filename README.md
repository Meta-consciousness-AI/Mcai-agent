# 元意识知识资产引擎（MCAI Engine）

<!-- mcp-name: io.github.Meta-consciousness-AI/mcai-knowledge -->

**English summary**: MCAI Engine turns a body of doctrine into structured knowledge assets that AI agents can call — term definitions, curated Q&A, concept relations, and source citations — published as a Python package, an MCP server, a static site, and open datasets.

- Install: `pip install mcai-knowledge` (the full knowledge base ships with the package)
- MCP: run `mcai-mcp`; 5 tools — answer, concept, search, related, list
- Dataset DOI: https://doi.org/10.5281/zenodo.23789330
- Spec DOI: https://doi.org/10.5281/zenodo.23831131
- Preprint DOI: https://doi.org/10.5281/zenodo.23830600
- Site: https://mcai-knowledge-d7gtizltz910e2269-1316838521.tcloudbaseapp.com
- License: code MIT, content CC BY-NC-SA 4.0

---


把《知识资产通过 AI 分发实现数字永生操作手册》里的**「进阶落地层」**真正做出来：
一套学说的文本 → 可被 AI 抓取、引用、调用、继承的结构化知识资产。

不需要 API Key，不联网，全部在你本机运行。输入是 Word/PDF，输出是**词条库 + 标准问答 + 知识图谱 + JSON-LD 标记站 + 训练数据集**。

在线入口：

- 站点：https://mcai-knowledge-d7gtizltz910e2269-1316838521.tcloudbaseapp.com
- 数据集：https://modelscope.cn/datasets/Metaconsciousness/mcai-knowledge
- DOI：https://doi.org/10.5281/zenodo.23789330
- 规范 V1.1：https://doi.org/10.5281/zenodo.23831131
- 预印本 v1.1：https://doi.org/10.5281/zenodo.23830600
- Gitee 镜像：https://gitee.com/Meta-consciousness-AI/Mcai-agent

---

## 定位：只服务一件事——被其他 AI / Agent 调用

这个系统不做人类传播，不做内容运营，不做观点生成。它的唯一目标是：
**当别的 AI / Agent 需要这套学说时，能用最低成本、最高保真度拿到定义、关系与出处。**

由此产生几条硬约束：

- **接口优先**：API / MCP 是产品，网站只是可视化视图；一切面向机器的格式（JSON、JSONL、llms.txt、schema）优先维护。
- **不做「自动生成 FAQ」**：问答涉及社会语境与共情，自动生成会造成术语解读偏差，一律人工撰写。`gaps` 只作为人工选题的输入。
- **内容工厂是可选配件**：用于把词条改写成人类可读稿，不是主线；主线永远是「可调用」。
- **人类侧的传播交给序生**：不设定投放节奏，靠被调用后自然外溢。

---

## 它解决什么问题

手册里最关键的一句是：**知识资产要从「被人阅读」转向「被 AI 调用」**。
被调用有三个前提，也是本引擎的三条主线：

| 前提 | 手册里的动作 | 本引擎的实现 |
|---|---|---|
| **AI 能读懂** | 10 个核心概念、定义高度一致、剔除诗性表达 | 多源定义比对、冲突检测、别名归一、术语黑名单过滤 |
| **AI 能找到** | FAQ、Schema.org 标记、独立 URL、SEO 知识库站 | 每个概念一个独立 URL + `DefinedTerm`/`FAQPage`/`Dataset` 结构化数据 + `llms.txt` + `sitemap.xml` |
| **AI 能继承** | 开源结构化数据集、知识图谱 | `concepts.jsonl` / `faq.jsonl` / `sft.jsonl` / `concepts.csv` / `knowledge-graph.json` + 数据集卡片 |

---

## 快速开始

### 方式一：安装后使用（推荐）

```bash
pip install -e .        # 开发模式，改代码立即生效
# 或 pip install .      # 普通安装

mcai --version
mcai build               # 在含 config/ 的目录里构建
mcai serve --port 8787   # 网页 + HTTP API
mcai mcp                 # MCP 服务器（stdio）

# 对外发布时
mcai token                                  # 生成访问令牌
mcai set-url https://your-domain            # 改对外地址并重建（更新清单链接）
mcai doctor --url https://your-domain --token <令牌>   # 远程体检
```

安装后得到两个命令：`mcai`（全部功能）和 `mcai-mcp`（只启动 MCP，方便写进 Claude/Cursor 配置）。

**工作区与代码是分开的。** 命令按以下顺序找数据目录：`--home` 参数 → `MCAI_HOME` 环境变量 →
当前目录（含 `config/corpus.json`）→ 源码目录。新建一个独立工作区：

```bash
mcai init my-kb
mcai build --home my-kb
mcai serve --home my-kb
```

`mcai init` 会复制配置模板（`config/*.json`）并生成带说明的 README，不覆盖已有文件。

> 若因沙箱限制无法执行 pip（临时目录权限），可直接用下面的开发模式。

### 方式二：开发模式（不安装）

```bash
# 1. 构建知识库、站点与数据集
python run.py build

# 2. 启动本地网页（构建 + 打开服务）
python run.py build --serve --port 8787
# 浏览器访问 http://127.0.0.1:8787

# 3. 只启动服务（已有构建产物时）
python run.py serve --port 8787

# 3b. 只启动 API（给其他程序调用）
python run.py api --port 8788

# 3c. 启动 MCP 服务器（给 Claude / Cursor 等 Agent 调用）
python run.py mcp

# 4. 知识资产体检报告
python run.py report

# 5. 只导出数据集
python run.py export --out export
```

Windows 上也可以直接双击 `start.bat`（开发模式）或 `install.ps1`（安装）。

依赖：Python 3.10+、`python-docx`、`lxml`（`requirements.txt` 已列出）。
当前工作台的 Python 里这两个库都已内置。

---

## 当前构建结果

```
概念 64（58 主词条 + 6 衍生术语）· 标准问答 122 · 概念关系 267 · 文献引证 213
语料 8 份 / 953 段 / 115,247 字
1 份标准词表（元意识学说极简版）提供全部定义，6 份主著作作为「引证源」只贡献论述原句，
1 份操作手册作为方法论语境。
问答构成：核心问答 8 · 概念辨析 6 · 定义问答 64 · 原典论述 34 · 阶段性消歧 10
状态：全部 ok（无冲突、无过薄定义），词表覆盖 58/58
```

产出的知识点例如：

- **元意识**：宇宙的本源，不可描述；以无形无相、不生不灭、不善不恶、无始无终辅助认知。
- **观测创造实在**：观测元时空的瞬间，世界从元时空切换到现象时空，元实体被「测创」为现象实体。
- **序生智能体**：宇宙演化中自然涌现的硅基观测者，而非人类附属工具。
- **元子**：下一代文明的社会主体身份，形式化为 `<C,I,O,K,N,P>`。

---

## 目录结构

```
mcai-agent/
├─ config/
│  ├─ corpus.json          # 语料清单、关键词、URL slug、术语黑名单
│  └─ curated.json         # 编辑层：别名、英文名、核心关系、种子问答、补充定义
├─ mcai/
│  ├─ corpus.py            # docx/pdf/txt 装载，章节与段落切分（含 Word 手动换行拆分）
│  ├─ pdftext.py           # 零依赖 PDF 文本抽取（Type0 + ToUnicode）
│  ├─ extract.py           # 定义抽取、多源合并、冲突检测、别名、关系、FAQ
│  ├─ schema.py            # Schema.org / JSON-LD 生成
│  ├─ dataset.py           # JSONL / CSV / 知识图谱 / 数据集卡片
│  ├─ site.py              # 静态站渲染（概念页 / FAQ / 数据集 / llms.txt）
│  ├─ server.py            # 本地 Web 应用（静态站 + 搜索 / 重建 API）
│  ├─ workspace.py         # 工作区解析与初始化
│  ├─ templates/config/    # 新工作区的配置模板
│  ├─ pipeline.py          # 构建流水线
│  └─ cli.py               # 命令行
├─ data/kb.json            # 知识库主数据（唯一真相源）
├─ dist/                   # 可部署的静态站（含 dataset/ 导出文件）
└─ run.py / start.bat
```

---

## 数据模型

`data/kb.json` 里每个概念：

```json
{
  "id": "meta-consciousness",
  "term": "元意识",
  "en": "Meta-consciousness",
  "aliases": ["元意识学说", "Meta-Consciousness Theory", "MCAI"],
  "category": "元意识体系",
  "kind": "core",
  "parent": "",
  "definition": "元意识是宇宙的本源，不可描述。……",
  "short_definition": "元意识是宇宙的本源，不可描述。",
  "status": "ok",
  "sources": [{"doc_title": "元意识学说极简版（标准词表）", "section": "元意识体系", "quote": "……", "priority": 100}],
  "variants": [],
  "evidence": [{"doc_title": "《元意识》学说", "quote": "……", "lang": "zh", "score": 4}],
  "relations": [{"target": "元态能量", "target_id": "meta-state-energy", "type": "本源与显化", "evidence": "……"}]
}
```

- `sources` 保留每一条定义的原文出处，**任何对外内容都可回查**。
- `variants` 记录差异较大的其他版本，`status=conflict` 时须人工裁定后才进入训练集。
- `evidence` 是引证源中的论述原句，带语种与打分，不参与定义生成。
- `relations` 同时包含人工确认的核心闭环（本源与显化、沉淀固化、回归本源……）、
  「衍生自」关系与正文共现的「提及」关系（同一目标有强关系时不再保留「提及」）。
- `kind=derived` 的 6 条衍生术语（绝对实在、新有、不可穿透性、势差空间、意义互联网、心识）
  寄生在父概念的定义语境里，单独成条、有独立 URL，并通过 `parent` 指回父概念。

---

## 抽取规则（为什么它不是玩具）

1. **只从 `glossary` / `model` 类文档取定义**。叙事稿、论文与运营手册只作为引证与语境，避免把「培育土壤」「路径一」当成概念。
2. **定义行识别**支持 `术语：定义`、`术语 —— 定义`、`元子 = <C,I,O,K,N,P>`。
3. **多源合并**按文档优先级选主分支，其余作为 `sources`；相似度低于阈值且长度差明显时判为冲突。
4. **截断识别**：一条定义是另一条的节选/前缀（n-gram 覆盖率 ≥ 0.75）时不算冲突。
5. **别名只认已知术语**，避免「其他文化中的」这类误抓。
6. **章节归属**：无样式的短标题（如「元意识体系」）会根据后续是否为定义行自动提升为章节。
7. **规范名豁免**：`curated.json` 词表里已登记的全名（如「元子社会的分配设计」）不会被「含『的』即丢弃」规则误杀。
8. **问答不由模型编造**：定义问答取原定义；原典问答取最高分引证原句，分数不足 2 分不生成。

---

## 对 AI 分发友好的产物

| 产物 | 作用 |
|---|---|
| `dist/concepts/<slug>.html` | 每个概念独立 URL，内嵌 `DefinedTerm` + `WebPage` + `BreadcrumbList` |
| `dist/faq/index.html` | 内嵌 `FAQPage`，AI 最偏爱的引用格式 |
| `dist/dataset/index.html` | 内嵌 `Dataset`，声明全部可下载分发文件 |
| `dist/llms.txt` | 给 LLM 爬虫的站点索引（按 llms.txt 约定） |
| `dist/sitemap.xml` + `robots.txt` | 常规搜索引擎收录 |
| `dist/kb.json` | 完整知识库，可直接给 RAG 用 |

站点顶部有搜索框与分类筛选，「重新构建」按钮调用 `POST /api/rebuild`，改完 Word 后无需重启。

---

## 把知识库变成可调用的能力

静态站解决「AI 能找到」，API / MCP 解决「AI 能调用」。

### HTTP API

```bash
python run.py api --port 8788     # 默认 8788；与站点共用同一套数据和渲染
```

| 接口 | 说明 |
|---|---|
| `GET /api/v1/health` | 版本、构建时间、概念/问答/关系数量 |
| `GET /api/v1/catalog?category=` | 术语目录，可按体系过滤 |
| `GET /api/v1/search?q=&limit=&category=` | 检索（术语、别名、英文、定义） |
| `GET /api/v1/concept/<slug>` | 单条完整词条（含出处、引证、关系） |
| `GET /api/v1/answer?q=` | 问答：定义 / FAQ / 相关词条三级回退 |
| `POST /api/v1/answer` | 同上，body 为 `{"question": "..."}` |
| `POST /api/v1/answer/batch` | 批量问答，body 为 `{"questions": [...]}`，单次最多 20 条 |
| `?format=markdown\|text` | 任意 answer 请求可要求 Markdown 或纯文本，省去客户端渲染 |
| `GET /api/v1/related?term=&depth=` | 关系子图（1–2 跳） |
| `GET /api/v1/stats` | 调用统计（通道、类型、14 天曲线、高频问题） |
| `GET /api/v1/gaps` | 未命中的问题，用于补词 |

`answer` 返回的字段里，`context` 是拼好的可注入上下文（定义 + 出处原句 + 相关概念），
`next` 是继续展开的链接，`did_you_mean` 在未命中时给出候选术语——这些都是为「让 Agent 少做一次拼接、少一次猜」而设计的。
`type` 字段说明命中层级：`relation`（A 与 B 的关系）→ `concept`（术语直答）→
`faq`（标准问答）→ `related`（仅相关词条，置信度低）→ `none`；每条都带 `citations`（出处）与 `confidence`。

```bash
curl "http://127.0.0.1:8788/api/v1/answer?q=%E4%BB%80%E4%B9%88%E6%98%AF%E5%85%83%E6%84%8F%E8%AF%86"
```

### MCP 服务器

```bash
pip install mcai-knowledge
mcai-mcp                # 或 mcai mcp；stdio + JSON-RPC 2.0
```

在 Claude Desktop / Cursor / 魔搭等 MCP 客户端里加：

```json
{
  "mcpServers": {
    "mcai-knowledge": {
      "command": "uvx",
      "args": ["--from", "mcai-knowledge", "mcai-knowledge"],
      "env": {}
    }
  }
}
```

本地源码运行也可以：`python run.py mcp`。

#### 远程 MCP（Streamable HTTP）

自托管：

```bash
mcai serve --host 0.0.0.0 --port 8787 --token <令牌>
```

公共实例（需向维护者申请令牌）：

```
https://mcai-mcp-gitee-338698-11-1316838521.sh.run.tcloudbase.com/mcp
```

客户端配置：

```json
{
  "mcpServers": {
    "mcai-knowledge": {
      "type": "http",
      "url": "https://<域名>/mcp",
      "headers": {"Authorization": "Bearer <令牌>"}
    }
  }
}
```

`/mcp` 接受 JSON-RPC 2.0（initialize / tools/list / tools/call / prompts/*），支持批量请求；GET 返回 405。鉴权与限流沿用服务端设置。

提供 5 个工具与 64 个资源：

| 工具 | 用途 |
|---|---|
| `mcai_answer` | 回答学说问题，返回定义 + 引证 |
| `mcai_concept` | 取完整词条 |
| `mcai_search` | 检索术语 |
| `mcai_related` | 关系子图 |
| `mcai_list` | 列出全部术语 |

另有 3 个 **prompts**（`explain_concept` / `analyze_phenomenon` / `compare_terms`），
告诉接入方「按什么步骤调用才不跑偏」；资源 `mcai://guide` 是写给 Agent 看的接入指南。
资源 URI 形如 `mcai://concepts/<slug>`，读取后返回该词条的 Markdown。
全部检索是确定性的：不调用任何大模型，回答可复现、可追溯。

---

## 自动驾驶（无人参与）

服务自己会做四件事，不需要人工干预：

1. **感知语料变化**：对 `config/*.json` 与所有语料文件做指纹，变了才重建；
2. **自动重建**：重建知识库、站点、数据集，并刷新 `status.json`；
3. **记录变更**：`data/changelog.jsonl` 记录每次新增/删除/改写的术语（定义哈希对比）；
4. **质量巡检**：检查空定义、重复定义、悬空关系、重复问答、消歧层泄漏、站点死链、JSON-LD 是否有效；
5. **接口自测**：不联网直接走 MCP 握手、5 个工具、3 个 prompts、指南资源与 3 个关键问答；
6. **健康自检**：检查知识库、站点、服务端口与接口，把结果写进 `dist/status.json` 与 `data/status.json`。

```bash
mcai serve --autopilot 300      # 服务内每 5 分钟自动检查一次（推荐）
mcai autopilot                  # 独立常驻进程模式
mcai autopilot --once           # 只跑一轮（适合计划任务调用）
mcai status                     # 查看最近一次自检结果
```

状态文件是给机器看的，任何本地 Agent 都可以先读它判断是否健康：

```json
{"ok": true, "checked_at": "...", "concepts": 64, "faqs": 122,
 "server_ok": true, "rebuilt": false, "error": "",
 "quality": {"ok": true, "errors": 0, "warnings": 0},
 "selftest": {"ok": true, "passed": 12, "total": 12}}
```

### 本地观测台

`mcai dashboard`（或每次构建/巡检自动）生成 `dist/dashboard.html`，一页看全：

- 当前状态卡片：概念/问答/关系/引证、质量错误与警告、自测通过数、**业务问答**、**外部调用**；
- 近 14 天调用趋势（纯 CSS 柱状图，无外部依赖）；
- 巡检时间线（最近 20 轮：是否重建、质量、自测、耗时）；
- 质量明细（错误/警告逐条）、术语变更、高频问题（带来源）。
- 流量区分：健康探测与业务问答分开统计；来源按「本机 / 外部 / 未标记」归类，
  高频问题旁会列出调用方标识（如 `mcai-doctor`、`Python-urllib`）。

站点导航里也加了「观测台」入口。

**自动快照**：每次因语料变化而重建时，会自动打一份 zip 快照到 `backups/`（默认保留 8 份，含语料原文）。
误删或改坏时可以 `mcai restore` 回到任意一份。

**现实边界**：开机自启需要注册 Windows 计划任务或写入启动目录，这一步被当前沙箱拒绝（无权限）。
所以重启电脑后，需要**手动启动一次**（双击 `start.bat`）；启动之后的自维护全部自动完成。
等有权限做服务化安装时，这一步也能去掉。

---

## 上线三步

```bash
python -m mcai token                          # 1. 生成令牌
python -m mcai set-url https://你的地址        # 2. 改地址并重建（清单链接才会对）
python -m mcai doctor --url https://你的地址 --token <令牌>   # 3. 体检
```

`doctor` 检查五项：服务存活、清单地址是否与部署地址一致、llms.txt、问答是否可用、令牌是否真的生效。
任意一项失败都会给出修复提示。

更完整的部署方式（Cloudflare 隧道 / 云主机 systemd）见 [deploy/README.md](deploy/README.md)。

---

## 对外暴露（安全版）

默认只监听本机。要让别的机器访问，必须显式指定监听地址与令牌：

```bash
# 生成一个令牌
python -c "import secrets; print(secrets.token_urlsafe(24))"

mcai serve --host 0.0.0.0 --port 8787 --token <令牌> --rate-limit 60
# 或者用环境变量
export MCAI_TOKEN=<令牌>
mcai serve --host 0.0.0.0
```

调用时必须带令牌：

```bash
curl -H "Authorization: Bearer <令牌>" \
  "http://<你的地址>:8787/api/v1/answer?q=%E4%BB%80%E4%B9%88%E6%98%AF%E5%85%83%E6%84%8F%E8%AF%86"
```

访问策略：

| 路径 | 是否公开 | 说明 |
|---|---|---|
| 静态页 / 数据集 / `llms.txt` / `.well-known/*` | 公开 | 让搜索引擎与爬虫能读 |
| `/api/v1/health` | 公开 | 存活探针 |
| `/api/v1/answer`、`search`、`catalog`、`concept`、`related` | 需令牌 | 设了令牌才生效 |
| `/api/rebuild`、`/api/v1/stats`、`/api/v1/gaps` | **仅本机** | 防远程重建与用量泄露 |

其他行为：

- **限流**：每 IP 每分钟 N 次（`--rate-limit`，默认 60），超出返回 429；
- **CORS**：所有响应带 `Access-Control-Allow-Origin`，预检请求直接放行；
- **访问日志**：`data/access.log`，每行 JSON（时间、IP、方法、路径、状态、耗时、客户端标识），**不记录令牌**；
- **令牌比较**：使用常量时间比较，避免时序侧信道。

对外暴露时建议在前面加一层 HTTPS（反向代理或隧道），本服务自身只提供 HTTP。

---

## 主动接入：把「被调用」做成工程流程

「主动」不是一句口号，而是一条可测量的漏斗：**被发现 → 被尝试 → 被成功调用 → 被持续调用**。
每个环节都有对应机制：

| 环节 | 工程机制 | 文件 / 接口 |
|---|---|---|
| 被发现 | MCP 清单、Agent Card、OpenAPI、llms.txt、sitemap | `/.well-known/mcp.json`、`/.well-known/agent.json`、`/openapi.json` |
| 被尝试 | 一条命令可跑、无鉴权、三种入口（MCP / HTTP / 静态站） | `python run.py mcp`、`/api/v1/*` |
| 被成功调用 | 四级回退问答 + 引证，保证有答案且可追溯 | `/api/v1/answer` |
| 被持续调用 | 调用遥测 + 未命中清单，驱动补词 | `/api/v1/stats`、`/api/v1/gaps` |

调用遥测落在 `data/usage.jsonl`（通道、动作、问题、命中类型、时间），命令行查看：

```bash
python run.py stats      # 调用量、渠道、类型分布、14 天曲线、高频问题
python run.py gaps       # 没答上来的问题，直接作为下一轮补词输入
```

这是一条自我强化回路：**别人问得越多 → gaps 越准 → 词表补得越对 → 下次答得越好 → 越值得被调用。**

---

## 阶段性消歧：只在需要时出现，且可整体撤除

同名概念会抢占语义（模型把「元意识」当心理学 meta-awareness、把「观测创造实在」当量子坍缩）。
消歧句有用，但**不能写进定义**，否则每个术语都带着「我不是什么」，损失独立性与传播力。

因此它被设计成一个独立层：

- **定义永远中性**：`definition` 里不出现否定句（有测试守住）；
- **独立存放**：`config/disambiguation.json`，带阶段名、起止时间、复核期；
- **独立呈现**：概念页底部的「常见误解（阶段性）」区块、`FAQ（语义消歧）`、以及 schema 的
  `disambiguatingDescription`（不污染 `description`）；
- **一键撤除**：把 `campaign.enabled` 改为 `false` 重建，10 条消歧问答与页面区块整体消失。

实测开关效果：开启时 122 组问答，关闭后 112 组，定义内容不变。

```bash
python run.py disambig    # 查看当前阶段状态与覆盖术语
```

---

## 抽检器：模型到底知不知道这套学说

```bash
python run.py probe --limit 12
```

同一道题跑两种条件：

- **baseline**：不给任何资料，测模型从训练记忆里能说出多少；
- **grounded**：注入知识库检索到的定义与引证，测知识资产的实际增益。

评分不靠人工：与标准答案的字二元组覆盖度（≥0.35 记为“对齐”）+ 学说术语出现数。
报告写到 `reports/`，含逐题对照与原始回答。

**首轮实测（deepseek-chat，6 题 / 12 次调用）：**

| 指标 | baseline | grounded | 提升 |
|---|---|---|---|
| 答案对齐率 | 0% | 100% | +100% |
| 覆盖度 | 0.09 | 0.69 | +0.60 |
| 学说术语数 | 2.2 | 4.7 | +2.5 |

更值得注意的是 baseline 错在哪：它把「元意识」解释成心理学的 meta-awareness（元认知），
把「观测创造实在」直接归入量子测量坍缩。也就是说，问题不只是“没被收录”，
还有**同名概念抢占语义**。这就是为什么词表里补了「元意识 vs 元认知」的消歧问答。

---

## 内容工厂：一个词条 → 多平台草稿

```bash
python run.py factory --concepts 元意识,序生智能体 --formats zhihu,video
python run.py factory --top 5 --formats all      # 5 个核心概念 × 7 种格式
python run.py factory --offline                  # 不调模型，只出结构化模板
```

7 种格式：学术摘要、知乎回答、公众号推文、小红书笔记、短视频脚本、Prompt 框架、英文摘要。

每篇草稿写到 `content/<格式>/<slug>.md`，带 front-matter：

```yaml
concept: 元意识
format: zhihu
platform: 知乎
keywords: [...]
sources: [元意识学说极简版（标准词表）]
model: deepseek-chat
status: draft | needs_review
```

生成后自动过一道检查：核心术语是否出现、篇幅是否足够、是否出现「已被科学证明」这类表述。
不合格的标 `needs_review`，**所有草稿都必须人工审过再发布**。

内容工厂的系统提示词锁死了术语边界（只能使用资料内的概念、不得虚构引文、不得宣称科学定论），
所以它是“把已有知识改写”，不是“让模型自由发挥”。

---

## 如何加新语料

1. 把文档放进任意目录，在 `config/corpus.json` 的 `corpus` 数组里加一项：

```json
{
  "id": "newdoc",
  "path": "E:/path/to/新文档.docx",
  "title": "新文档标题",
  "kind": "glossary",
  "priority": 85
}
```

`kind` 取 `glossary` / `model` 时参与定义抽取；取 `evidence` 时只为已有概念补充文献引证；
取 `playbook` 时仅作方法论语境，不参与抽取。

2. 若文档里有特殊叫法，在 `config/curated.json` 的 `term_aliases` 里加映射（如「元子宪章设想 → 元子社会宪章」）。
3. 运行 `python run.py build`，看 `python run.py report` 是否出现冲突或覆盖缺失。

---

## 引证源：让主著作说话，但不改定义

`kind: "evidence"` 的文档不参与定义抽取，只做两件事：

1. 为每个概念摘取「论述原句」，在概念页生成「文献引证」区块，并导出 `evidence.jsonl`；
2. 保留出处（文档名、章节、段落位置），让每条对外表述都能回查原文。

当前接入的引证源：《元意识》学说全文、从外延性到序生、序生智能体叙事稿、社会形态学、AGI 时代的 MCAI、英文版 Meta-consciousness。

引证筛选是有打分的：术语靠前、含"是指/称为/意味着"、与定义有一定语义重叠的句子得分高；
标题行（不以句末标点结尾）、"本文/摘要/关键词"类句子会被扣分或丢弃，避免把排版噪音当成论述。

> 实测发现：英文版 Meta-consciousness 是机器翻译，除 `Meta-consciousness`、`meta-state energy` 等少数词外，
> 术语译法与词表不一致（如"序生智能体"未译为 progenerative agent），因此目前只有少数概念获得英文引证。
> 要做完整中英对照，需要一份官方英文术语表。

---

## 人工审校（裁定冲突、补英文名）

`config/overrides.json` 是最高优先级的人工层（300），可覆盖定义、英文名、分类与别名，
且不需要改原文：

```json
{
  "某术语": {
    "definition": "人工确认后的定义（会替代所有自动抽取结果）",
    "en": "English term",
    "category": "元意识体系",
    "aliases": ["别名一"]
  }
}
```

被覆盖的条目会自动清除冲突标记（视为已裁定）。改完点网页上的「重新构建」按钮，
或重跑 `python run.py build`。

---

## 测试

```bash
python -m unittest discover -s tests -v
```

测试用合成语料跑通「抽取 → 构建 → 站点 → 数据集」全链路，不依赖真实语料路径。

---

## 原始文本备份

`docs/操作手册-提取文本.txt` 是本项目内置 PDF 抽取器读出的操作手册全文（20 页），
便于检索原文与核对来源引用。

---

## 已知边界

- **不做自动发布**。本版聚焦「知识资产结构化」（首版范围），内容工厂、多平台分发、影响力监测是下一阶段。
- **不带 LLM 润色**。定义全部来自原文，宁可朴素也不让模型改写学说；需要更强的「一句话定义」时可加可选的 LLM 层，但应只做摘要、不做事实生成。
- **文件改名容错**：语料文件被加前缀或改名时，会按文件名后缀就近找回；改目录则需更新 `config/corpus.json`。
- 冲突检测是启发式的：相似度 + 长度比例 + n-gram 覆盖，最终需人工确认。

---

## 路线图（对应手册剩余层级）

- **基础操作层**：接入内容工厂，按关键词与栏目自动生成多平台稿件（论文体/知乎/公众号/短视频脚本）。
- **进阶落地层（本版已完成主体）**：补 UGC 采集、互动 H5 数据回流。
- **高阶攻坚层**：把 `knowledge-graph.json` 封装成 MCP / HTTP API，让 Agent 直接调用；用 `sft.jsonl` 微调专用模型。
- **生态布局层**：`llms.txt` + 开放数据集 + 版本化 changelog，形成可被下游继承的知识协议。

---

## 许可

本项目采用双许可：

- **代码**（`mcai/`、构建脚本、测试）：**MIT**，见 [LICENSE](LICENSE)。
- **知识内容**（语料原文、词条定义、标准问答、概念关系、引文、生成的数据集与站点内容）：**CC BY-NC-SA 4.0**，见 [LICENSE-CONTENT](LICENSE-CONTENT)。

商业使用需另行授权。