# 研究：让搜索引擎与 AI 找到知识库

> 时间：2026-11-20
> 起因：在豆包搜索「元意识学说」相关术语时，豆包先尝试查询我们的知识库，但查询失败。
> 目标：让百度、谷歌、必应，以及豆包、Kimi、DeepSeek 等模型在涉及以下词时，能找到、读懂并引用我们的知识库：
> 元意识、元意识学说、元意识 AI、Meta-Consciousness Theory、Meta-consciousness-AI、MCAI。

## 一、先分清三种「被搜到」

| 类型 | 谁在找 | 决定因素 |
|---|---|---|
| 传统搜索收录 | 百度、谷歌、必应 | 抓取、索引、站点权重、外链 |
| AI 搜索/爬虫 | 豆包 Bytespider、GPTBot、ClaudeBot、PerplexityBot | robots、llms.txt、页面可读性、索引 |
| 模型回答里引用 | 各类大模型 | 训练语料、搜索工具返回、第三方引用 |

豆包这次失败，可能卡在第二层或第三层，不一定是站点打不开。

## 二、现状诊断

### 已经具备

- 站点对主流爬虫 UA 均返回 200（Baiduspider、Bytespider、GPTBot、Googlebot 实测）；
- `robots.txt` 允许全站抓取，并声明 sitemap；
- 有 `llms.txt`、`llms-full.txt`、`.well-known/mcp.json`、`.well-known/agent.json`；
- 每个术语有独立 URL、JSON-LD（DefinedTerm/FAQPage/Dataset）；
- PyPI、GitHub、Gitee、Zenodo、PhilArchive、Glama、mcprush 等已有入口。

### 明显不足

1. **搜索收录弱**：用站点域名做 `site:` 查询，没有稳定返回知识库页面；目前主要被搜到的是 PyPI、Glama、掘金等第三方页；
2. **域名权重低**：`*.tcloudbaseapp.com` 是云开发默认域名，搜索引擎与模型对它的信任度低；
3. **实体信号弱**：缺少一个「关于元意识学说 / MCAI」的实体页，缺少 Organization、sameAs 的完整声明；
4. **外链少**：除代码托管与 MCP 目录外，缺少可被搜索引用的第三方页面；
5. **数据曾经过时**：`llms.txt` 之前写 64 概念/122 问答，与当前 65/126 不一致（已重建修正）；
6. **没有 Search Console / 百度站长 / IndexNow 的持续提交**；
7. **豆包失败原因未知**：需要看它的具体报错或访问日志，才能判断是「没索引」「访问超时」「需要登录」还是「它把知识库当成另一种接口」。

## 三、策略：三层 + 一个闭环

### 第一层：可抓取

- robots 允许所有主流与 AI 爬虫；
- sitemap 自动更新；
- 页面不依赖 JS 渲染；
- 每个术语独立 URL、canonical、JSON-LD；
- `llms.txt` / `llms-full.txt` 与知识库同步；
- `.well-known/mcp.json`、`agent.json` 保持最新。

### 第二层：可发现

- Google Search Console、Bing Webmaster、百度站长验证；
- 提交 sitemap，配置 IndexNow；
- 做 6 个「查询词落地页」：元意识、元意识学说、元意识 AI、Meta-Consciousness Theory、Meta-consciousness-AI、MCAI；
- 每个页面首屏直接回答「是什么、不是什么、出处」；
- 站内互链：首页 → 术语 → 问答 → 数据集；
- 自定义域名（长期）：默认域名换掉，权重才能积累。

### 第三层：可信任

- 实体页：Organization / Person / DefinedTermSet，`sameAs` 指向 GitHub、Gitee、PyPI、Zenodo、PhilArchive、Glama；
- 第三方引用：PyPI 描述、GitHub README、掘金/知乎/公众号、MCP 目录、学术预印本；
- 学术页：Zenodo DOI、PhilArchive 条目、论文；
- 避免：关键词堆砌、假百科、垃圾外链、cloaking。

### 闭环：测量

每月一次查询矩阵：

| 查询词 | 百度 | 谷歌 | 必应 | 豆包 | Kimi | DeepSeek |
|---|---|---|---|---|---|---|
| 元意识 | | | | | | |
| 元意识学说 | | | | | | |
| 元意识 AI | | | | | | |
| Meta-Consciousness Theory | | | | | | |
| Meta-consciousness-AI | | | | | | |
| MCAI | | | | | | |

记录：是否出现我们的站点/术语/DOI；是否引用；引用的是哪一页。

## 四、30 天计划

### 第 1 周：修基础设施

- 重建站点（65 概念 / 126 问答）并上线；
- 新增「关于元意识学说 / MCAI」实体页；
- 补 Organization、WebSite、sameAs 结构化数据；
- 验证 Google / Bing / 百度站长，提交 sitemap；
- 配置 IndexNow。

### 第 2 周：做查询词落地页

- 6 个词各一页，首屏给定义、边界、出处；
- 每页加 FAQPage / DefinedTerm 结构化数据；
- 与现有术语页、问答页互链；
- 英文页同步。

### 第 3 周：外链与第三方

- PyPI / GitHub / Gitee README 加关键词与站点链接；
- 掘金、知乎、公众号各发一篇「元意识学说是什么」；
- 更新 MCP 目录（Glama、mcprush、Smithery、ModelScope 等）；
- 检查 Zenodo / PhilArchive 元数据。

### 第 4 周：测量与迭代

- 跑一遍查询矩阵；
- 看 Search Console / 百度站长收录；
- 看服务器日志里 Bytespider、GPTBot、Baiduspider 的访问；
- 根据结果补页面或补外链。

## 五、豆包失败的真实原因（2026-11-20 截图确认）

截图显示豆包的动作是：

1. 读取 `mca knowledge` 技能中的 `SKILL.md`；
2. 执行 `curl -s -m 5 -X POST http://127.0.0.1:8787/...`；
3. `ls -la /home/user/.doubao/...`；
4. 在 `/tmp` 与技能目录里 grep 内容；
5. 最后说明：「知识库的本地服务当前没在运行（127.0.0.1:8787 连接被拒）」。

所以这次不是搜索收录问题，而是：

- **技能指向本机服务**，手机上 `127.0.0.1` 是手机自己，不是电脑；
- 技能脚本是 Windows PowerShell，手机端是 Linux 环境，本来也跑不了；
- 它退回到用户上传的两份 PDF，靠原文推导答案。

结论：豆包这次失败 = **本地端点 + 平台不匹配**，与百度/谷歌是否收录无关。

## 六、两个独立问题

| 问题 | 性质 | 解决方向 |
|---|---|---|
| 豆包技能调不到知识库 | 配置与平台适配 | 做「远程技能」或配置远程 MCP |
| 搜索引擎/AI 搜索找不到站点 | 收录与权重 | 实体页、站长提交、外链、查询词落地页 |

两件事要分开做，不能混在一起。

## 六、判断标准

- 百度/谷歌/必应搜索「元意识学说」，首页能看到我们的站点；
- 豆包/Kimi/DeepSeek 回答相关问题时，能引用我们的术语或 DOI；
- Search Console 有稳定收录；
- 日志里有 AI 爬虫持续访问。

## 变更记录

- 2026-11-20：建立。
