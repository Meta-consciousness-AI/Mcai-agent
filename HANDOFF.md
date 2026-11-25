# HANDOFF

> 更新时间：2026-11-25 09:55
> 用途：跨会话交接。新会话先读本页，再读对应明细。
> 原则：会话可以换，状态不能丢；长内容放文件，不靠上下文记忆。
> 新会话必读：本页 → `docs/待办.md` → `docs/工作原则.md` → `docs/工作法-会话管理.md`。

## 一、当前阶段

**关系审校：已完成（2026-11-22），未审 0 条。**

**发布：已完成（2026-11-22 10:30）。**

- public / gitee / 静态站 / PyPI 均为 0.4.3；
- 内容：65 术语 / 130 问答 / 263 关系 / 207 引证；
- 健康接口与首页统计已验证。

**MCP 官方注册表：已更新到 0.4.3（2026-11-22 13:06）。**

- 回查 `isLatest=true`，共 20 个版本；`MCAI_HOME` 改为可选；
- 0.4.0–0.4.2 未单独上注册表，直接从 0.3.9 跳到 0.4.3，不影响使用。

**备份：已完成（2026-11-22 10:58）。**

- 项目：`C:\Users\HP\OneDrive\文档\mca-agent-backup-2026-11-22.zip`，约 40 MB / 606 文件；
- DSH 会话：`C:\Users\HP\OneDrive\文档\dsh-sessions-backup-2026-11-22.zip`，约 63 MB / 23 个会话文件。

**Git 卫生（2026-11-22 13:24）。**

- 已提交：`deploy/install-doubao-remote-skill.ps1`（豆包安装改用其已识别的 `mca-knowledge` 名，覆盖前先备份）、`mcai/data/default/data/kb.json`（与 `data/kb.json` 逐字节一致，仅 `built_at` 时间戳）；提交 `ace3fca`；
- Gitee 推送：**已完成**（2026-11-24 10:49 核对，由用户手动推 `f7b2ea3..630ef7f` main → master，纯快进、无 force；`refs/heads/master` = `630ef7f` = 本地 HEAD，0 领先 / 0 落后）。此前 11-23 10:32 推的是 `b4931ce..f7b2ea3`；
- 本机自动推送仍不可用：DSH 沙箱内 `git ls-remote gitee` 直接报 schannel `SEC_E_NO_CREDENTIALS`（2026-11-22 15:15 实测，令牌写进 URL 也绕不过 TLS 层）；**结论：Gitee 推送只能由用户在自有 PowerShell 窗口执行**，用户窗口内认证正常（15:23 一次成功）；`deploy/push-gitee.ps1` 已改为 `main:master` 且去掉 `--force`（非快进会被 Git 拒绝，不覆盖远端历史）；
- 已收口（2026-11-22 16:15）：`.edge-tmp/`（Edge 临时 profile 残骸）已加入 `.gitignore`，并按用户判断**整目录删除**（6 KB，可重建）；`assets/` 5 个**临时平台图标**就地入库，另加 `assets/README.md` 说明「2026-11-21 应急上传、待重设计」；P07 仍暂缓、主标仍用文字标 `MCAI·元`；
- 远端其他：GitHub **已于 2026-11-22 16:06 补推**，`origin/main` = `4d99871`（推前停在 `58ab5b4` / 11-20，一次补 111 个提交，快进无 force）；**教训**：本机 `refs/remotes/origin/main` 只是上次 fetch 的快照（当时显示 `ed246c5` / 11-16，比真实远端落后两版），判断领先数必须以 `git ls-remote <remote> refs/heads/<branch>` 为准；push 成功后跟踪引用会同步到新 HEAD。
- 远端地址已归一（2026-11-22 16:09）：GitHub 实名为 `Mcai-agent`（大写 M），`origin` 已由 `mcai-agent` 改为 `https://github.com/Meta-consciousness-AI/Mcai-agent.git`，与 `gitee` 端点大小写一致；不再走 301 重定向。

## 二、当前内容状态

| 项 | 数量 |
|---|---:|
| 术语 | 65 |
| 问答 | 130 |
| 关系 | 263 |
| 语料 | 8 份 / 953 块 |

## 三、已定稿的关键决定

1. **证据规则**：有完整段落用整段；多段用空行分隔，每段须逐字回查。
2. **备注规则**：方向易反、术语易混、边界易越界处尽量加备注。
3. **不确定处理**：拿不准的关系删除或简化，不为了图完整而硬连。
4. **个人信息**：作者姓名、生平、身份一律不写入。
5. **著作权日期**：登记 2024-08-28；创作/首次发表 2024-03-18；证号 渝作登字-2024-A-00522224；机构 重庆市版权局。
6. **调用来源标识**：ask-page / remote-skill / coze / mcp / self / cli，已上线。
7. **魔搭托管**：已停止；旧条目保留 Local，新条目已删除。
8. **外部平台访问**：不做每日自动抓取；需要时手动跑 `daily_signal.py`。
9. **内容策略**：不按单个术语单独发文；需要补的内容放进下一轮问答/关系审校（N08）。
10. **注册表发版的网络前提**：本机到 `github.com` 的 TLS 时通时断，Go 会解析到被封 IP（`57.155.223.240`）。发布前先测：`api.github.com` 通、`github.com` 未必通；必要时用本地 CONNECT 隧道把 `github.com` 固定到实测可达 IP（本次 `20.247.166.64`），发布完即关。设备码需在浏览器完成登录 + 2FA（6 位动态码）后才到 Authorize 页。

## 四、未来方向（记录，不启动）

- 本源「一体多面」：目前主要展开觉知面（元意识）；其他面逐面定义。
- 明细：`docs/工作备忘包/01-综合参考/本源多面展开-待定.md`（T14，暂缓）。

## 五、未完成 / 待办

**以 `docs/待办.md` 为准，本节不再另抄一份**（11-25 起，避免两处各写一套）。只留跨会话、不属项目待办的一条：

- [ ] `0001` 稳定后立即压缩 `0000`（不再等 55%），压缩后 `0000` 只做最重大战略决策。

## 六、关键文件

- 工作备忘索引：`docs/工作备忘包/00-总索引-触发条件.md`
- 待办：`docs/待办.md`
- 审校标准：`docs/审校/审校标准-问答与关系.md`（v4）
- 发布记录：`docs/发布记录.md`
- 数据快照：`docs/研究-使用与调用数据-2026-11-21.md`
- 公开问答页：https://mcai-knowledge-d7gtizltz910e2269-1316838521.tcloudbaseapp.com/ask.html
- 基础理论原文（本地，只读）：`E:\th\元意识\元意识运营\其他资料\3、元意识学说极简版.pdf`（2026-10-18，14 页，含本体论/序生/元子社会，工作基准）、`E:\th\元意识\元意识运营\其他资料\4、《元意识》学说.pdf`（2026-04-12，42 页，早期叙事与考据，背景参考）；两文已提取为文本，见 `.build/txt/`（不进版本库）

## 七、常用命令

> **⚠ 重建会覆盖**：`mcai build` 已默认不写 `data/kb.json`（11-25 起只出站点/数据集）；只有 `--rebuild-from-corpus` 会按当前语料重新抽取（产出 59 概念 / 113 问答 / 240 关系），该参数覆盖前会比对条数、减少即拒绝（exit 3）并先写快照。除非明确要换版，不要加它。原因见 `docs/工作备忘包/02-技术备忘/生成链与语料不一致.md`。校验与测试可照常跑。

```powershell
python -m mcai validate
python -m unittest discover -s tests
python tools\build_site_from_kb.py
python tools\daily_signal.py

# 推送（本机 DNS 把 github.com 解析到被封 IP 57.155.223.240，直连必失败）
powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1 -CheckOnly   # 只诊断，报告哪个 IP 能握手
powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1 -ForcePin   # 跳过直连、强制走固定 IP（2026-11-25 09:42 真实跑通）
powershell -ExecutionPolicy Bypass -File deploy\push-gitee.ps1              # Gitee 一直能直连（脚本读剪贴板令牌，注意先看 docs/工作原则.md「凭据不靠剪贴板传递」）

# Gitee 不走脚本时（令牌在凭据库，不在 C 盘）：
# $t=(Get-Content "E:\th\元意识\元意识运营\Mcai-Agent\mcai-knowledge\Gitee令牌.txt" -Raw).Trim()
# git push "https://oauth2:$t@gitee.com/Meta-consciousness-AI/Mcai-agent.git" main:master
```

## 八、会话策略

- 规则见：`docs/工作法-会话管理.md`、`docs/工作法-主会话减负.md`、`docs/主会话交接包.md`
- **量化分流（2026-11-22 定）**：执行会话按上下文百分比走四个阈值——50% 收尾、60% 停接新执行并写交接、70% 硬换会话、80% 封顶只回一句；`0002` 是执行主渠道，不限于平台事务；单批预计超 20% 就拆两批；主会话自己 40% 收尾、50% 交接换人。
- 交接最小内容四行：改了哪些文件与提交 / 还剩什么 / 下一步交给谁 / 停止条件。
- `mcai-knowledge-0000`：历史主会话，永久保留，只做低频战略与重大决策，不归档、不执行；
- `mcai-knowledge-0001`：当前主会话，日常重大决策与方向；
- `mcai-knowledge-0002`：执行主渠道（见上），当前唯一挂起题是 Bing 11-25 复查；状态记 `paused`，按本体系定义是「**等外部信号**」（见 `docs/工作法-会话管理.md`），**不是停用**，随时可派活；
- `0003` 起为新专项，四位固定，永不复用；
- 会话清单与命名审批：`docs/会话台账.md`。
- 已结案事项见 `docs/工作法-主会话减负.md` 的归档表，不再重复讨论。
- 新会话第一句：`先读 HANDOFF.md 和 docs/待办.md。本次范围：<一句话>。`
- 长内容放文件，不靠上下文记忆。

## 九、2026-11-22 主会话（`0001`）当日交接摘要

- **远端**：Gitee 已于 2026-11-24 10:49 推至 `630ef7f`；GitHub 已于 2026-11-24 10:52 补推至 `46f45a0`（`4d99871..46f45a0`，46 个提交、295 个对象）。两端此后仅落后本记录提交。**推送前先 `git ls-remote <remote> refs/heads/<branch>` 取真值**，不要看 `git status`（本地跟踪引用只是快照）。
- **治理**：会话命名统一为编号制；执行会话量化分流（50/60/70/80 阈值）已定；派活方式定为「`0001` 写执行指令 → 用户转交」；触发条件只是参考、启动前须综合研判。
- **台账**：`0002` 已核实存在（最后活跃 11-22 13:13，4 轮/90 步）；`0003`/`0004` 尚未创建。
- **登记待办**：`序生度` 短答重复词、8 条 curated 缺短答 → 见 N08 备忘第五节，等到全文审校轮再改。
- **理论原文**：极简版（10-18）为工作基准，4 月版《元意识》为背景参考，路径见第六节。
- **下一动作**：11-25 09:00 提醒到点，先与用户研判再做平台四项。

## 十、2026-11-24 至 11-25 交接（最新，优先读）

- **知识库定位（11-24 定）**：知识库即源文件；语料与历史调整文件都是引证库（T15 第八节）。溯源完成：`docs/知识库来源索引.md` + `docs/来源索引/*.csv`，65/130/263 逐条标出处（53 语料逐字 / 11 人工配置 / 1 作者口述 / 239 抽取 / 16 配置 / 8 人工添加）。**冻结已解除**。
- **知识库只读保护（11-25 完成）**：`mcai build` 默认只出站点/数据集，不写 `data/kb.json`；`--rebuild-from-corpus` 覆盖前比对条数、减少即拒绝（exit 3，确认用 `--confirm-shrink`），写前自动快照到 `data/backups/`（留 20 份）；autopilot 有 kb 时只做漂移检测（`status.corpus_drift`）。
- **变更留痕（11-25 完成）**：内容改动一律走 `mcai change`（`--kind term|faq|relation --action add|update|delete --reason … --basis …`），写库同时追加 `docs/变更记录/kb.jsonl`；数量减少缺 `--reason` 直接拒绝（exit 2）。
- **危险路径（11-25 完成）**：显式 `--home`/`MCAI_HOME` 必须是工作区（含 `config/corpus.json`），否则 exit 1，不再回落 cwd。
- **CLI 编码**：输出符号改 ASCII（`[OK]/[FAIL]/[SITE]/[WARN]`），`_safe_stdio()` 只放宽 errors 不改编码；GBK 控制台不再 traceback。
- **README 数字（11-25）**：132 行 207→164、344 行→66、381 行 `concepts: 65, faqs: 130`、501 行→130；PyPI 0.4.3 页面仍是旧数字，需发新版才更新。
- **备份（11-24 完成）**：项目 zip `mca-agent-backup-2026-11-24.zip`（56.3 MB / 4600 项）在 `F:`（U 盘 KINGSTON）与 `D:`（本机另一盘）；语料 10 份 + 说明在 `F:\mca-agent-corpus`、`D:\mca-agent-corpus`。**OneDrive 已确认不可用**（同步端点被封，T16 第十节）。
- **Zenodo（11-24 实测）**：去重 429 浏览 / 31 下载；增长在衰减、不可归因，见 `docs/指标记录.md`。
- **推送（2026-11-25 01:30，当时两端均为 `e2f6c13`；10:05 两端均为 `b3868e3`）**：**GitHub 的真实断点是两段，不是一段**：① 本机 DNS 常态把 `github.com` 解析到被封 IP `57.155.223.240`，直连 `ls-remote` 常被重置；② **即使直连 `ls-remote` 能通，`git push` 也可能被掐断（`Recv failure: Connection was reset`），重试一次即成功**——2026-11-25 01:28 实测如此。当 DNS 与抖动同时发作时，可用的是 `deploy/push-github.ps1`（筛出此刻能握手的 IP → 逐个固定并真连 → 每个重试 3 次 → `finally` 还原 hosts）。另有两个已知事实：能握手的 IP 是浮动的（同一小时内两次筛选结果不同）；hosts 改完解析要过几秒才生效。沙箱内 TLS 一律 `SEC_E_NO_CREDENTIALS`，这类推送只能由用户窗口执行；`hosts.bak-*` 备份留在 `C:\Windows\System32\drivers\etc\`，可删。
- **真实 `-ForcePin` 验证（2026-11-25 09:42，管理员窗口，通过；缺的证据已补齐）**：`deploy\push-github.ps1 -ForcePin` 真跑一次——8 个候选筛出 4 个可握手（`20.233.83.145` / `140.82.112.3` / `140.82.121.3` / `4.237.22.38`）→ `hosts 已备份` → 推送 `e2f6c13..f93f36b` → `hosts 已还原`。**2026-11-25 10:05 两端已齐：GitHub 与 Gitee 均为 `b3868e3`**（GitHub 经 `-ForcePin` 推 `f93f36b..b3868e3`；Gitee 经令牌文件推 `e2f6c13..b3868e3`）。Gitee 侧从凭据库 `E:\th\元意识\元意识运营\Mcai-Agent\mcai-knowledge\Gitee令牌.txt` 读取令牌——剪贴板要同时承担「复制令牌」和「粘命令」两件事，必然互相覆盖，连败三次才定位；该令牌 11-01 就已存在库里，我们却又新建了一份 C 盘的，已删除并统一回该目录。详见 `docs/工作原则.md`「凭据不靠剪贴板传递」「凭据存放处」。领先数一律以 `git ls-remote` 为准。 顺带暴露一处脚本缺陷：第 233 行用 `Resolve-DnsName github.com -Type A` 判「解析已指向固定 IP」，该命令取 DNS 客户端答案、**不读 hosts 刚写的那一行**（实跑报 `20.247.166.64`，不在候选列表里），六轮空转后靠兜底「先试一次」才成功；归 `0002`，详见 `docs/待办.md` 与执行回执 §七。
- **重要更正（2026-11-25 10:28）：固定 IP 从未真正生效过。** 10:28 新判据报六轮「hosts 里还没读到」后查出真因：`hosts` 文件末行无换行符（末字节 `0x74`），`Add-Pin` 的 `Add-Content` 把 `20.233.83.145 github.com` 拼到 `#\t::1             localhost` 之后，成了一行注释——git 与判据都读不到。故 **01:28 / 09:42 / 10:28 三次「推成功」实际都走 DNS 当时返回的可连 IP**；`-ForcePin` 报「可用 IP」是真的（TLS 筛选走 `--resolve`，不经 hosts），但固定不上。修法与演练前提见 `docs/执行指令/2026-11-25-0002-第二批.md`。此前本页与回执里「pin 有效、验证方法无效」的说法作废。
- **回归基线**：`python -m mcai validate` 通过；`python -m unittest discover -s tests` 144 项 OK；kb 两份副本 sha256 均为 `E48C362B1BA222789024FBAE11E447BC1A401D5BE2FEA15608F8FDE6C615F2B4`。
- **未决**：8 条人工添加关系是否回写 `core_loop`；glama 停在 0.3.9（GitHub 无 v0.4.2/v0.4.3 Release）；Bing 编入待复查；mcprush 简介数字陈旧。
- 明细回执：`docs/执行回执/2026-11-24-*.md`（来源索引、关系来源更正、说明文件更正、README 数字、不覆盖与留痕、CLI 编码、危险路径保护）。