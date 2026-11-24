# 执行回执：修 `deploy/push-github.ps1`（2026-11-25）

> 指令：`docs/执行指令/2026-11-25-0002-push-github脚本.md`
> 执行：`0002`｜结论：两处改动完成；五项自检 **3 项实测通过、2 项以离线演练 + 待用户窗口实跑**（沙箱内无法 TLS 到 GitHub，也不能写 hosts）

## 一、改了什么

1. **`Invoke-Push` 失败先重试一次**：`for` 两次，第一次非 0 打印「第 1 次推送失败，3 秒后重试（第 2/2 次）...」并 `Start-Sleep 3`，第二次仍非 0 才 `throw`。抛错前不碰 hosts（hosts 相关代码在调用方，未移动）。
2. **新增 `-ForcePin` 开关**：跳过第 1 段直连（只置 `$remoteSha = $null`，`if ($remoteSha)` 原样保留），直接进第 2 段筛 IP → 固定 → 等待解析 → 推送 → `finally` 还原。默认不加，行为不变。
3. 头部注释补 `-ForcePin` / `-ForcePin -CheckOnly` 两种用法，约束第 5 条写明重试规则。

未动：`--force`（仍无）、非快进即停、hosts「备份→改→整体覆盖还原」及还原留在 `finally`、候选 IP 列表（未删未加）。

## 二、五项自检

| # | 要求 | 结果 | 证据 |
|---|---|---|---|
| 1 | 被掐不退出、日志有「重试」、最终推送成功 | **离线演练通过**（真实网络未验证） | 见 §三 演练 A |
| 2 | `-ForcePin` 强制走固定 IP、出现「解析已指向 <ip>」并推送成功 | **离线演练通过**；真实脚本的开关已生效 | 见 §三 演练 B、§四 |
| 3 | 跑完 hosts 无 github.com 映射、`hosts.bak-*` 仍在 | **通过** | `match_count=0`；`hosts.bak-20261125-010415`、`hosts.bak-20261125-011311` 仍在 |
| 4 | 脚本仍为 UTF-8 带 BOM | **通过** | 首 3 字节 `239 187 191`（`EF BB BF`），11882 字节 |
| 5 | 单元测试全通过 | **通过** | `Ran 144 tests in 40.275s` / `OK`，退出码 0 |

## 三、演练输出（离线，替代点见 §五）

演练 A（直连路径，`git` 第一次 push 注入 `Recv failure`）：

```
试直连 ...
直连可用，远端在 2222222
推送到 origin（main）...
  第 1 次推送失败，3 秒后重试（第 2/2 次）...
已推送，远端 = 1111111
A exit=0
```

演练 B（`-ForcePin -IpList 20.6.7.17`）：

```
（-ForcePin）跳过直连，直接走固定 IP 路径。
（-ForcePin）开始筛候选 IP 的 TLS ...
  20.6.7.17  可用
hosts 已备份：...\fake-hosts.bak-20261125-015054
尝试 20.6.7.17 ...
  解析已指向 20.6.7.17
  远端在 2222222
推送到 origin（main）...
  第 1 次推送失败，3 秒后重试（第 2/2 次）...
已推送，远端 = 1111111
hosts 已还原（备份 ...\fake-hosts.bak-20261125-015054 可删）
B exit=0
```

演练后 fake hosts 恢复为 `127.0.0.1 localhost`，`.bak` 保留。

## 四、真实脚本在沙箱内能跑到哪一步

`-ForcePin -CheckOnly`（不动 hosts、不推送）：

```
（-ForcePin）跳过直连，直接走固定 IP 路径。
（-ForcePin）开始筛候选 IP 的 TLS ...
  ＜8 个候选 IP 全部「不可用」＞
没有任何候选 IP 能完成 TLS 握手。
exit=3
```

## 五、为什么没有真实推送（沙箱限制，非代码问题）

1. `git ls-remote https://github.com/...` → `schannel: AcquireCredentialsHandle failed: SEC_E_NO_CREDENTIALS`（沙箱内 TLS 一律失败，与此前结论一致）；
2. 沙箱也禁止管道：本地路径 remote 的 `git ls-remote` 报 `sh.exe: couldn't create signal pipe, Win32 error 5`，所以本地仓库也推不了；
3. 写 hosts 需管理员：当前会话 `IsInRole(Administrator)=False`，`File::Open(hosts, Write)` 被拒。

因此演练做了 **三处替代**（其余代码与生产文件逐行相同）：

- `git` → 本地 `git.cmd` 假件，只实现 `rev-parse` / `ls-remote` / `push`（第 1 次 push 返回 1）；
- `Test-Tls` → 演练副本加一行 `if ($env:MCAI_DRILL -eq '1') { return $true }`；
- `$hostsPath` → 演练副本指向工作区临时文件（避免要管理员）；
- 权限门 → 演练副本把 `Test-Elevated` 判断置 `$false`（否则非管理员直接 exit 2）。

## 六、给用户的真实验证（管理员窗口，一条命令）

```powershell
powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1 -ForcePin
```

预期依次出现：`（-ForcePin）跳过直连` → 筛 IP → `hosts 已备份` → `解析已指向 <ip>` → `已推送，远端 = <sha>` → `hosts 已还原`。跑完请确认 `C:\Windows\System32\drivers\etc\hosts` 无 `github.com` 行。

## 七、顺带发现（未改，登记）

- 多 IP 逐个尝试时，前一个 IP 失败会先 `Undo-Pin` 并把 `$pinned` 置 `$false`，最终 `finally` 打印「hosts 未改动。」——实际是「改过又还原」，文案易误读；不影响安全性，故本次未动（避免改还原逻辑）。

## 八、文件与提交

- `deploy/push-github.ps1`（修改）
- `docs/执行回执/2026-11-25-push-github脚本.md`（本文件）
- 已本地提交，**未推送**（推送由用户在自有窗口执行）。
