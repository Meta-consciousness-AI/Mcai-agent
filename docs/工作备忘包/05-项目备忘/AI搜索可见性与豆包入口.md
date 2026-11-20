# AI 搜索可见性与豆包入口

> 状态：待启动（2026-11-20 记录）
> 关联：[研究-AI搜索可见性](../研究-AI搜索可见性.md)
> 原则：先解决确定性高的入口问题，再做长期的搜索权重。

> 基线测量：[AI搜索可见性-基线](AI搜索可见性-基线.md)

## 一、已经确认的事实

1. 豆包失败不是因为站点打不开：
   - Baiduspider、Bytespider、GPTBot、Googlebot 访问站点均 200；
   - robots.txt 允许全站。
2. 豆包失败是因为技能指向本机：
   - 技能 `mcai-knowledge` 的 endpoint 是 `http://127.0.0.1:8787/api/v1`；
   - 手机上 127.0.0.1 是手机自己；
   - 技能脚本是 Windows PowerShell，手机端跑不了。
3. 搜索收录弱：
   - `site:` 查询没有稳定返回知识库页面；
   - 目前主要曝光在 PyPI、Glama、掘金等第三方页。

## 二、两条工作线

### A. 豆包/手机端入口（短期，确定性高）

三个方案：

1. **远程技能包**：新建一个不依赖本机的技能，直接调用
   `https://mcai-mcp-public-338698-11-1316838521.sh.run.tcloudbase.com/api/v1/answer`；
2. **远程 MCP**：如果豆包支持自定义 MCP，配置
   `https://mcai-mcp-public-.../mcp`；
3. **仅限豆包 PC**：保持本机服务运行，手机端不用。

建议先做 1：远程技能包，Windows/Linux 双脚本，手机可直接 curl。

### B. 搜索引擎与 AI 搜索可见性（长期）

见研究文档的 30 天计划：

1. 站点同步 65 概念 / 126 问答；
2. 新增「关于元意识学说 / MCAI」实体页；
3. 补 Organization、sameAs、FAQPage 结构化数据；
4. Google Search Console、Bing Webmaster、百度站长验证与 sitemap 提交；
5. 6 个查询词落地页；
6. 第三方引用与 MCP 目录更新；
7. 每月查询矩阵。

## 三、优先级

1. 远程技能包（能立刻让手机豆包可用）；
2. 实体页 + 站长提交（决定长期被搜到）；
3. 查询词落地页与外链（慢功夫）。

## 四、暂缓

- 问答 122 条、关系 270 条的逐条审校暂停；
- 已审完的改动可以先上线，后续再慢慢改。

## 变更记录

- 2026-11-20：建立。

## 五、进展（2026-11-20）

- 百度站长：无法添加 `*.tcloudbaseapp.com` 站点，提示「该主域可添加站点数量超过限制」；账号内无旧站点可删，判断为共享主域配额限制。百度路径暂缓，等自有域名。
- Bing Webmaster：站点此前已添加成功；已补交 `/about.html` URL；已重新提交 sitemap；IndexNow 已推送 70 个 URL，返回 202。
- IndexNow key：`5e8c6744f39f84fd94acd507a6bfd0e9`，已写入站点生成器，重建不会丢失。
- 待观察：Bing 的 sitemap 处理与 about 收录。

## 六、远程技能包（2026-11-20）

- 目录：`skills/mcai-knowledge-remote/`
- 组成：`SKILL.md` + `bin/mcai_client.py` + `bin/query.sh` + `bin/query.ps1` + `README.md`
- 特点：不依赖本机、不需要 API Key、Python 标准库、POSIX/Windows 双包装；
- 已测试：`answer`、`batch`、`search`、`concept`、`related` 均可返回；
- 冷启动较慢，默认超时 90 秒；
- 安装脚本：`deploy/install-doubao-remote-skill.ps1`（支持 -DryRun / -Remove）；
- 待办：装进豆包实测，确认手机端/桌面端都能调用。

### 扣子商店（2026-11-20）

- 已发布公开智能体「元意识学说助手」；
- 链接：https://www.coze.cn/store/agent/7702301472461242409?bot_id=true
- 插件：MCAI 元意识学说知识库（mcaiAnswer / mcaiSearch）；
- 无痕窗口可打开，对话正常；
- 触达范围：扣子用户，不含豆包用户。

### 公开问答页（2026-11-20）

- 链接：https://mcai-knowledge-d7gtizltz910e2269-1316838521.tcloudbaseapp.com/ask.html
- 手机实测可用，回答带出处；
- 调用公网 API，不依赖本机；
- 已接入首页导航、sitemap、llms.txt；
- 已知限制：冷启动 30–90 秒；公网 API 尚未做应用层限流。
