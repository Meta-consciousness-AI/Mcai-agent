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
- **2026-10-29 16:51｜TDQS 提升到 4.5/5.0**
  0.2.4 补齐工具分工、语料边界、参数示例与注解后，Glama TDQS 从 3.9 → **4.5/5.0**
  （v0.1.2 release；mcai_answer 4.6、concept/list 4.5、search 4.4、related 4.3）。
- **2026-10-29 17:4x｜0.2.5：完整知识库进包**
  PyPI 包内置完整 64 概念 / 122 问答（159 KB wheel），外部安装即得全量内容，不再依赖演示库。
  PyPI / GitHub / MCP 注册表 / Glama 均更新到 0.2.5。
- **2026-10-29 22:3x｜国内稳定站点上线（腾讯云 CloudBase）**
  站点：https://mcai-knowledge-d7gtizltz910e2269-1316838521.tcloudbaseapp.com
  默认域名、免备案；canonical 与 sitemap 已切到该域名。
  Bing Webmaster 已验证站点并提交 sitemap（处理中）。
  百度搜索资源平台因共享主域 tcloudbaseapp.com 配额已满，暂时无法添加站点。
- **2026-10-30 00:0x｜国内平台状态**
  - 魔搭 MCP 广场：已收录（mcai-knowledge-mcp，uvx 配置）
  - ModelScope 数据集：已公开（Metaconsciousness/mcai-knowledge）
  - Gitee 镜像：已导入（Meta-consciousness-AI/Mcai-agent）
  - 文心智能体平台：创建入口已于 8 月 31 日下线
  - 腾讯元器：首页公告「平台停止服务」
  - 国内智能体平台路线暂停，转向协议层渠道（MCP / 数据集 / 站点）
- **2026-10-30 12:0x｜国际/国内渠道补齐**
  - 0.2.6：PyPI / MCP 注册表英文元数据；Glama 同步构建
  - Zenodo DOI：10.5281/zenodo.23789330
  - 扣子智能体：https://www.coze.cn/store/agent/7702301472461242409?bot_id=true
## 协作约定（2026-10-30 起）

- 每天 12:00、00:00 定时提醒休息（已创建 schedule）。
- 连续工作约 2 小时，主动提醒休息 15–30 分钟。
- 用户说「休息一下」时，视为重新计时。
## 行文观察（样本 1，仅记录，不作风格结论）

- 2026-10-30《把思想学说做成 AI 能调用的知识资产》成稿 vs 原稿：
  - 开头加「范式分水岭」定调，引入自有术语「序生智能体」；
  - 把判断句 soften（「不是模型笨」→「不是模型的问题」）；
  - 增加画面感表达（「语义海洋所淹没」）；
  - 结尾升维到 AGI / 《思想教科书》/「星空已在前」，带谦逊限定（「无人区」「认知出入」）。
- 待更多样本后，再判断哪些是稳定偏好、哪些是一次性选择。
- **2026-10-30 15:0x｜Gitee 镜像决策**
  Gitee 自动镜像需绑定/授权 GitHub，当前网络不可达，放弃该路径。
  Gitee 仓库保留导入时的版本，不影响任何对外渠道；后续如需要，用 Gitee 私人令牌手动推送。
- **2026-10-30 16:3x｜英文知识库决策**
  暂不做英文版知识库（术语层/全文）。理由：翻译是二次创作，术语偏差会沿英文材料扩散，纠正成本高；当前内容仍在演进，双库维护负担大；海外调用需求未验证。
  国际渠道维持现状：元数据英文，内容中文。
  重新评估的前提：先决条件是「元意识学说在中文语境已形成可观测影响力」（被引用、被讨论、被采用），在此之后才考虑；届时仍需 1) 官方英文术语表经作者逐条裁定，或 2) 出现明确的海外调用需求。
- **2026-10-30 18:1x｜预印本发布（Zenodo Preprint）**
  标题：面向 AI 调用的学说知识资产化：方法与单案例研究 / Knowledge Assetization of a Doctrine for AI Invocation: Method and a Single-Case Study
  DOI：10.5281/zenodo.23801176（总 DOI 10.5281/zenodo.23801175）
  类型：Preprint；许可 CC BY-NC-SA 4.0；语言 Mandarin Chinese；关联数据集 DOI 10.5281/zenodo.23789330。
  ChinaXiv 因仅接受 cas.edu / 科研机构邮箱，未能提交。
- **2026-10-30 19:1x｜PhilArchive / PhilPapers 提交（待审核）**
  以个人账号（Hai Tan）提交，作者署名 Tan, Hai，摘要注明 MCAI Research Group 与公司。
  分类：Philosophy of Computing and Information；状态 Unpublished；附 PDF 与 Zenodo DOI 外链。
  平台提示：非学术邮箱投稿需人工审核，最长 1 个工作日。若被拒，保留 Zenodo 版本即可。

- **2026-10-31 07:2x｜评测基准暂缓**
  可核对评测（检索题/缺失题/一致性题）只做了样例，暂不推进。
  原因：评分口径、题目权威性、争议标注等未想清楚；避免制造「第二层解释」。
  主线仍为结构化检索语料；若日后重启，需先定：答案键规则、disputed 机制、与知识库的版本隔离。


- **2026-10-31 07:5x｜P0 完成（检索语料主线）**
  P0-1 出处精确化：修复拆分块 location 冲突（加 #序号），source 增加 char_start/char_end/origin；
    新增 provenance.jsonl 与 tools/verify_citations.py，语料来源 55/55 逐字命中、字符区间 100% 一致。
  P0-2 检索召回：归一化（全半角/繁简/标点/大小写）+ 错字容忍（difflib）；新增 6 条召回测试。
  P0-3 引用模式：HTTP `format=citations` 与 MCP `mcai_answer(format="citations")`，只返回出处。
  测试 90 条全通过。提交 bc3c44a / 560ff10。


- **2026-10-31 08:0x｜0.2.8 发布完成**
  PyPI / MCP 注册表 0.2.8；GitHub 4137e579；Glama 同步并构建成功（08:00）。
  内容：出处精确化（55/55 核验）、检索归一化与错字容忍、`format=citations` 引用模式。


- **2026-10-31 12:0x｜远程 MCP 上线（CloudBase 云托管）**
  服务：mcai-mcp-gitee；地址：https://mcai-mcp-gitee-338698-11-1316838521.sh.run.tcloudbase.com/mcp
  规格：1 核 2G，最小实例 0、最大 5；端口 8080；令牌由环境变量 MCAI_TOKEN 注入。
  已验证：GET / 200、initialize 200、tools/list 5、tools/call 正常、无令牌 401。
  旧的失败服务 mcai-mcp 已删除；新增 deploy/push-gitee.ps1 与 推送Gitee.cmd（Gitee 令牌经剪贴板读取）。


- **2026-10-31 13:3x｜P2 站点与数据集增强（已上线）**
  站点：每页 canonical + OG 标签；新增 llms-full.txt（全部定义/出处/核心关系/问答）。
  数据集：新增 relations.jsonl（270 条，core 18 / derived 6 / mention 246）。
  线上验证：首页、概念页、FAQ 页 canonical 正确；llms-full 200；relations.jsonl 200。


- **2026-10-31 13:4x｜第二语料复现完成（孙子兵法）**
  工作区 workspaces/sunzi：13 概念 / 17 问答 / 6 关系 / 9 引证；引文核验 13/13 逐字命中、字符区间一致。
  复现暴露并修复：中文数字开头术语被误杀（五事/九地）、txt 文档无唯一位置号、过短定义未识别。
  结论：方法可迁移；词表与核心关系仍需人工；规范 V1.1 需补「术语—原句对照表」与「数字开头术语」两条。
  详见 docs/复现案例-孙子兵法.md，提交 6defae0。


- **2026-10-31 13:5x｜第三语料复现完成（荀子·正名）**
  工作区 workspaces/xunzi：12 概念 / 5 问答 / 9 关系 / 12 引证；引文核验 12/12。
  暴露并修复：单字术语（性情名辞）被「至少两字」规则拒绝；关系问句只认多字术语。
  规范 V1.1 修订项增至四条：术语—原句对照、中文数字开头、人工登记单字、定义分层（原文句+编者释义）。
  主库不受影响（仍 64/122/270），103 条测试通过。提交 3ff9089。


- **2026-10-31 14:0x｜规范 V1.1 发布（内部）**
  新增四条：无词表文本先做术语—原句对照；允许中文数字开头术语；允许人工登记的单字术语；定义分层（definition_type=quote|editor + editor_note）。
  代码同步：Concept 增加 definition_type/editor_note；MCP 词条返回两字段；站点在 editor_note 存在时显示「编者释义（非原文）」。
  验证状态：三语料复现 + 远程 MCP 已列入「已验证」；定义分层留待道德经类文本验证（V1.2）。
  提交 7b9f6d7。


- **2026-10-31 14:2x｜第四语料复现完成（道德经，定义分层验证）**
  工作区 workspaces/daodejing：10 概念 / 8 问答 / 7 关系 / 10 引证；引文 10/10；全部 definition_type=editor。
  验证：answer 返回 definition_type 与独立 editor_note；词条页显示「编者释义（非原文）」；MCP 词条含两字段。
  新发现：同一经典版本差异（见素抱扑 vs 抱朴、水利 vs 水善利），引文必须按所据版本逐字保留，不能按通行本「更正」。
  规范 V1.2 待补：语料与引证记录 edition（版本/来源/校勘），多版本引证并存不合并不改字。
  提交 3c6983e。


- **2026-10-31 14:5x｜发布 V1.1（Zenodo）**
  预印本 v1.1：DOI 10.5281/zenodo.23830600（版本记录 23830600，文件 PDF，6 页，中英标题/摘要）。
  规范 V1.1：DOI 10.5281/zenodo.23831131（新记录，PDF 8 页，Report，CC BY-NC-SA 4.0，语言 zho）。
  两份均已 API 核对：版本号、文件、许可、关键词、语言正确。
  README 已补两条 DOI；V1.0 预印本记录保留（23801176）。

- **2026-10-31 15:0x｜Gitee 令牌已吊销**：`mcai-deploy`（projects 权限、永不过期）已删除；日后推送 Gitee 需重新生成令牌（脚本从剪贴板读取）。


- **2026-10-31 20:2x｜规范 V1.2（edition）实现完成**
  Source/Document 增加 edition；四份语料配置回填（元意识、孙子、荀子、道德经）。
  引用、MCP 词条、数据集 provenance、站点「定义来源」均显示版本；64/64 词条页带版本标注。
  修复：站点证据区块复用 quotes 变量导致定义引文的版本被覆盖。
  测试 107 通过；规范 V1.2 md/docx/pdf 已生成（8 页）。提交 16dcc8b、d07d2d5。发布待定。


- **2026-10-31 20:2x｜规范 V1.2 发布（Zenodo）**
  DOI 10.5281/zenodo.23836301，版本 1.2，文件 `规范-学说知识资产化-v1.2.pdf`，8 页；许可 CC BY-NC-SA 4.0，语言中文。
  描述含中英双段与 edition 说明；关键词新增「版本管理」「edition」。
  README 的 Spec DOI 已指向 1.2；V1.1 记录 23831131 保留。


- **2026-10-31 20:3x｜0.3.0 发布**
  PyPI 0.3.0（wheel 165 KB，包内 KB 含 edition/definition_type）；GitHub `184dcee`；MCP 注册表 0.3.0 已提交；Glama 已触发同步与构建（邮件已到）。
  打包脚本修正：构建 wheel 前把 data/kb.json 同步进 mcai/data/default，避免包内旧数据。
  人工裁定来源补 edition=「人工裁定」；测试 107 通过。


- **2026-10-31 20:5x｜数据集 v1.1 发布（Zenodo）**
  版本 DOI 10.5281/zenodo.23836789；文件 mcai-knowledge-dataset-v1.1.zip（9 个文件，含 relations.jsonl、provenance edition、README）。
  概念 DOI 23789330 始终指向最新版。Views 15 含本人访问与爬虫，Downloads 0，不能当作外部采用证据。


- **2026-11-01 09:1x｜规范 V1.3 发布（Zenodo）**
  DOI 10.5281/zenodo.23850554，版本 1.3，PDF 9 页，CC BY-NC-SA 4.0；关键词新增「多版本」「edition variants」。
  README 的 Spec DOI 已指向 1.3；V1.1/V1.2 记录保留。GitHub 推送与注册表因网络不通延后。


- **2026-11-01 09:2x｜决定：暂不铺量经典语料**
  结论：「先发」能拿到引用与习惯，「占位」拿不到排他；经典文本的问答模型本来就会，真正稀缺的是出处、术语边界、版本差异。
  做法：维持 3–5 部示范（孙子、荀子、道德经，必要时加一部带真实多版本的）；把方法做成可复制标准与工具；等 Zenodo 下载出现再谈扩张。
  依据：Zenodo 下载 0、GitHub Star 0、第三方提及 0（见 docs/指标记录.md 2026-11 复盘）。


- **2026-11-01 09:5x｜0.3.1 全渠道发布完成**
  PyPI 0.3.1（含 edition_variants、health 版本修复）；GitHub `866bf37`；MCP 注册表 0.3.1；Glama 同步与构建完成（邮件确认）。
  规范 V1.3 同日发布：DOI 10.5281/zenodo.23850554。


- **2026-11-01 10:1x｜Gitee 与云托管已恢复并升级到 0.3.1**
  Gitee 重新推送至 `32211d0`；CloudBase 云托管重建（部署 003，正常），远程 MCP initialize 与 /api/v1/health 均为 0.3.1，5 个工具可用。
  注：GitHub 在 `866bf37`，缺最后一个 docs 提交 `32211d0`（不影响代码）。


- **2026-11-01 16:2x｜远程 MCP 调用计数上线（0.3.2）**
  新增 `GET /api/v1/usage`（需 Bearer 令牌），返回 mcp_calls、by_action、by_day、last_call；同时在 stdout 打 `[usage] mcp <tool>` 供云端日志统计。
  云托管部署 004，initialize 显示 0.3.2，usage 接口实测可用。
  限制：计数存在容器内 data/usage.jsonl，重建或缩容会归零；要长期留存需读云端日志或外部存储。


- **2026-11-01 16:3x｜0.3.2 全渠道发布**
  PyPI 0.3.2；GitHub 与 Gitee 均为 `0d9103e`；MCP 注册表 0.3.2；Glama 已重建；云托管部署 004（initialize=0.3.2，/api/v1/usage 可用）。


- **2026-11-01 16:5x｜内容惯例与构建者渠道**
  决定：日后公众号/知乎每篇技术文章文末固定放 Coze 直达链接或二维码（零安装入口），形成惯例。
  构建者渠道先试 PulseMCP，两周观察；Smithery 因要求 OAuth 暂不合适；PulseMCP 对脚本 403，需浏览器提交。


- **2026-11-01 18:0x｜国内渠道首轮投放**
  掘金：https://juejin.cn/post/7702723478470377510
  知乎：https://zhuanlan.zhihu.com/p/2100281795400962883
  魔搭 MCP：描述、标签、托管类型（仅本地可用）已更新；3→4 浏览
  Coze：开场白 + 4 个预置问题，已重新发布到扣子商店
  V2EX 不可达、SegmentFault 短信收不到、腾讯云 MCP 广场关闭第三方上架；阿里云/火山待注册。


- **2026-11-01 18:1x｜国内渠道升级为工作重点**
  定位为「可达性」而非推广；渠道分三层（Agent/MCP 平台、开发者社区、RAG 工具生态）；每月扫描新渠道，攒 2–3 个再集中注册。
  待办：阿里云百炼、火山引擎、博客园、开源中国、CSDN；持续观察魔搭与 Coze。


- **2026-11-01 22:0x｜公开只读 MCP 实例上线**
  服务 mcai-mcp-public，地址 https://mcai-mcp-public-338698-11-1316838521.sh.run.tcloudbase.com/mcp
  无令牌可 initialize 与 tools/call；/api/rebuild、/api/v1/stats、/api/v1/gaps 均返回 403；版本 0.3.2。
  README 已补公开实例配置；可用于百炼、魔搭 Streamable HTTP、Smithery 等不需要令牌的接入。


- **2026-11-01 22:2x｜百炼接入公开 MCP**
  百炼控制台 MCP 管理 → 接入已有 MCP 服务 → 安装方式 http，配置公开地址；服务 mcai-knowledge 已启用，`mcai_answer` 工具测试成功。
  结论：百炼自定义 MCP 仅限本人账号内使用，没有第三方公开上架通道，不带来外部调用者；价值在于验证公开实例可用、可搭自有智能体。


- **2026-11-02 10:2x｜PhilArchive 重新提交（完整元数据）**
  11-02 上午站内搜索与作者页均无记录，邮箱也无审核邮件；随后按 /edit 流程重新提交：
  类型 Article、状态 Unpublished、作者 Hai Tan、语言中文、摘要完整、上传 v1.1 PDF、DOI 关联、分类 Philosophy of Computing and Information、6 个关键词。
  页面提示：审核最多 1 个工作日。
