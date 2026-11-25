# 推送到 GitHub 的 main 分支，或用 -Tag 只推一个标签。
#
# 为什么需要这个脚本：本机 DNS 常态把 github.com 解析到被封 IP（57.155.223.240），
# 直连基本必失败（Connection was reset / Empty reply from server）。
# 更麻烦的是：能完成 TLS 握手的 IP 是浮动的——2026-11-25 实测，
# 上一分钟通的 IP 下一分钟就被重置，所以「测一次、固定一个」不可靠。
# 因此脚本会：先列出所有能握手的 IP → 逐个固定并真连一次 → 连不上就换下一个。
#
# 用法：
#   管理员 PowerShell 里执行（改 hosts 需要管理员）：
#     powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1
#   只诊断，不改 hosts、不推送（普通窗口即可）：
#     powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1 -CheckOnly
#   指定候选 IP：
#     powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1 -IpList 1.2.3.4,5.6.7.8
#   强制走固定 IP 路径（跳过直连；只用于验证这条分支）：
#     powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1 -ForcePin
#   只验证固定 IP 分支的筛选结果、不改 hosts 也不推送（普通窗口即可）：
#     powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1 -ForcePin -CheckOnly
#   只推一个标签（走完全相同的筛 IP / 固定 / 还原流程，不做 push --tags）：
#     powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1 -Tag v0.4.4
#     powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1 -ForcePin -Tag v0.4.4
#
# 约束：
#   1. 不加 --force。非快进会被 Git 拒绝，遇到就停下查分叉原因；
#   2. hosts 用「备份→改→还原」而不是「删那一行」，保证不误伤文件里其他条目；
#   3. 还原放在 finally，push 失败或抛异常也会还原；
#   4. 本文件必须存成 UTF-8 带 BOM，否则 Windows PowerShell 5.1 按 GBK 读、中文注释变乱码、报「缺少引号」；
#   5. push 被掐断（Recv failure: Connection was reset）时自动重试 1 次、间隔 3 秒；两次都失败才抛错；
#   6. -Tag 只推指定的一个标签，绝不 push --tags；复核比的是标签对象的 sha，不是 HEAD。

[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [switch]$ForcePin,
    [string]$Tag,
    [string[]]$IpList
)

$ErrorActionPreference = "Stop"

$root      = Split-Path $PSScriptRoot -Parent
$remote    = "origin"
$branch    = "main"
$hostsPath = Join-Path $env:WINDIR "System32\drivers\etc\hosts"
$maxTries  = 3

# 推分支还是推标签：只换「推哪个 ref、查哪个 ref、跟谁的 sha 比」，流程其余部分完全共用
if ($Tag) {
    $refSpec    = "refs/tags/$Tag"
    $refRemote  = "refs/tags/$Tag"
    $whatToPush = "标签 $Tag"
}
else {
    $refSpec    = $branch
    $refRemote  = "refs/heads/$branch"
    $whatToPush = "分支 $branch"
}

# 候选 IP：2026-11-25 实测过的 GitHub 边缘地址，顺序只是偏好，脚本会自己挑能握手的
$candidates = if ($IpList) { $IpList } else { @(
    "20.233.83.145",
    "20.6.7.17",
    "20.205.243.166",
    "140.82.112.3",
    "140.82.113.3",
    "140.82.121.3",
    "4.237.22.38",
    "20.27.177.113"
) }

function Find-Git {
    $cmd = Get-Command git -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($p in @("C:\Program Files\Git\cmd\git.exe", "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe")) {
        if (Test-Path $p) { return $p }
    }
    throw "找不到 git"
}

function Find-Curl {
    $cmd = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $p = Join-Path $env:WINDIR "System32\curl.exe"
    if (Test-Path $p) { return $p }
    throw "找不到 curl.exe（Windows 10 1803+ 自带）"
}

function Test-Elevated {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $pr = New-Object Security.Principal.WindowsPrincipal($id)
    return $pr.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 强制指定 IP 完成一次 TLS 握手；只有返回 200 才算这个 IP 此刻可用。
# TCP 能连不算数——今天就是 TCP 通、TLS 被重置。
function Test-Tls([string]$ip) {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $out = & $curl -sS -o NUL -w "%{http_code}" --max-time 8 --resolve "github.com:443:$ip" https://github.com/ 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    return ($code -eq 0 -and "$out".Trim() -eq "200")
}

# 判断「hosts 固定是否真的生效」。不能用 Resolve-DnsName——它取的是 DNS 客户端的答案，
# 不读 hosts 里刚写进去的那一行（2026-11-25 09:42 实跑就是被它误导：固定 20.233.83.145，
# 它却连报六轮 20.247.166.64，白等约 5 秒后靠兜底才成功）。改用两条硬证据：
#   ① 从 hosts 文件里读回 `<ip> github.com` 这一行；
#   ② 对 github.com:443 做一次真实 TCP 连接（连接会走 hosts）。
function Test-HostsPin([string]$ip) {
    $pattern = '^\s*' + [regex]::Escape($ip) + '\s+github\.com(\s|$)'
    return (@(Select-String -LiteralPath $hostsPath -Pattern $pattern -ErrorAction SilentlyContinue).Count -gt 0)
}

function Test-GithubTcp {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $task = $client.ConnectAsync("github.com", 443)
        return ($task.Wait(2500) -and $client.Connected)
    }
    catch { return $false }
    finally { try { $client.Close() } catch { } }
}

# 取远端 ref 的 sha（分支或标签，由 $refRemote 决定）；失败时把 git 原话打出来，不吞错
function Get-RemoteSha {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $out = & $git -C $root ls-remote $remote $refRemote 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0) {
        Write-Host "    git ls-remote 失败：" -ForegroundColor DarkYellow
        ($out | Select-Object -First 4) | ForEach-Object { Write-Host "      $_" -ForegroundColor DarkYellow }
        return $null
    }
    $line = ("$out" -split "`n" | Where-Object { $_ -match "^[0-9a-f]{40}\s" } | Select-Object -First 1)
    if (-not $line) { return $null }
    return ($line.Trim() -split "\s+")[0]
}

# 取本地标签对象的 sha。附注标签的 refs/tags/<name> 指向 tag 对象（不是 commit），
# 所以推标签后要比对 tag 对象 sha；拿 HEAD 去比永远不相等。
function Get-LocalTagSha([string]$name) {
    if (-not $name) { return $null }
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $out = & $git -C $root rev-parse --verify "refs/tags/$name" 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0) { return $null }
    $line = ("$out" -split "`n" | Where-Object { $_ -match "^[0-9a-f]{40}$" } | Select-Object -First 1)
    if (-not $line) { return $null }
    return $line.Trim()
}

function Invoke-Push {
    Write-Host "推送 $whatToPush 到 $remote ..." -ForegroundColor Cyan
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $ok = $false
    for ($attempt = 1; $attempt -le 2; $attempt++) {
        if ($attempt -gt 1) {
            Write-Host "  第 1 次推送失败，3 秒后重试（第 2/2 次）..." -ForegroundColor DarkYellow
            Start-Sleep -Seconds 3
        }
        & $git -C $root push $remote $refSpec
        $code = $LASTEXITCODE
        if ($code -eq 0) { $ok = $true; break }
    }
    $ErrorActionPreference = $prev
    if (-not $ok) {
        throw "推送失败（凭据问题，或非快进被拒；本脚本不 force，不会覆盖远端历史）"
    }
}

function Add-Pin([string]$ip) {
    # hosts 的末行可能没有换行符（2026-11-25 实测：822 字节、末字节 0x74，即
    # `#\t::1             localhost` 后直接结束）。此时 Add-Content 会把新行拼到末行尾部，
    # 变成 `#\t::1             localhost20.233.83.145 github.com`——整行是注释，
    # git 和判据都读不到，等于没固定。所以先补换行，写完再回读确认。
    $bytes = [System.IO.File]::ReadAllBytes($hostsPath)
    $endsWithNewline = ($bytes.Length -gt 0 -and $bytes[$bytes.Length - 1] -eq 0x0A)
    $line = "$ip github.com"
    if ($bytes.Length -gt 0 -and -not $endsWithNewline) { $line = "`r`n" + $line }
    [System.IO.File]::AppendAllText($hostsPath, $line + "`r`n", [System.Text.Encoding]::ASCII)
    ipconfig /flushdns | Out-Null
    if (-not (Test-HostsPin $ip)) {
        throw "hosts 已追加但回读不到 `"$ip github.com`" 这一行，固定未生效（$hostsPath）"
    }
}

function Undo-Pin([string]$backup) {
    Copy-Item -LiteralPath $backup -Destination $hostsPath -Force
    ipconfig /flushdns | Out-Null
}

$git  = Find-Git
$curl = Find-Curl
$localSha = (& $git -C $root rev-parse HEAD).Trim()

if ($Tag) {
    $targetSha = Get-LocalTagSha $Tag
    if (-not $targetSha) {
        throw "本地没有标签 $Tag。先建标签（git tag -a $Tag -m `"…`"）再推。"
    }
    $targetLabel = "本机标签 $Tag"
}
else {
    $targetSha   = $localSha
    $targetLabel = "本机 HEAD"
}
$short = $targetSha.Substring(0, 7)

Write-Host "$targetLabel：$short" -ForegroundColor Gray
Write-Host "远端：$remote/$refRemote" -ForegroundColor Gray

# ---------- 0. 权限前置检查（改 hosts 必需），-CheckOnly 不检查 ----------
if (-not $CheckOnly -and -not (Test-Elevated)) {
    Write-Host ""
    Write-Host "改 hosts 需要管理员权限。请用管理员 PowerShell 重跑：" -ForegroundColor Red
    Write-Host "  powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1" -ForegroundColor Yellow
    Write-Host "（只想看哪个 IP 能用，普通窗口加 -CheckOnly 即可）" -ForegroundColor Gray
    exit 2
}

# ---------- 1. 直连能不能用（-ForcePin 时整段跳过） ----------
$remoteSha = $null
if ($ForcePin) {
    Write-Host "（-ForcePin）跳过直连，直接走固定 IP 路径。" -ForegroundColor Yellow
}
else {
    Write-Host "试直连 ..." -ForegroundColor Gray
    $remoteSha = Get-RemoteSha
}

if ($remoteSha) {
    Write-Host "直连可用，远端在 $($remoteSha.Substring(0,7))" -ForegroundColor Green
    if ($remoteSha -eq $targetSha) {
        Write-Host "远端已与本地一致，无需推送。" -ForegroundColor Green
        exit 0
    }
    if ($CheckOnly) {
        Write-Host "（-CheckOnly）直连可用，可正常推送。" -ForegroundColor Yellow
        exit 0
    }
    Invoke-Push
    $after = Get-RemoteSha
    if ($after -eq $targetSha) {
        Write-Host "已推送，远端 = $($after.Substring(0,7))" -ForegroundColor Green
        exit 0
    }
    throw "推送后复核不一致：远端 $after，$targetLabel $targetSha"
}

# ---------- 2. 直连不通：先筛出此刻能握手的 IP ----------
if ($ForcePin) {
    Write-Host "（-ForcePin）开始筛候选 IP 的 TLS ..." -ForegroundColor Yellow
}
else {
    Write-Host "直连不通，开始筛候选 IP 的 TLS ..." -ForegroundColor Yellow
}
$good = @()
foreach ($ip in $candidates) {
    if (Test-Tls $ip) {
        Write-Host "  $ip  可用" -ForegroundColor Green
        $good += $ip
    }
    else {
        Write-Host "  $ip  不可用" -ForegroundColor DarkGray
    }
}

if ($good.Count -eq 0) {
    Write-Host ""
    Write-Host "没有任何候选 IP 能完成 TLS 握手。" -ForegroundColor Red
    Write-Host "按顺序试：① 手机热点；② 你有代理则设 git http.proxy；③ 换一批候选 IP：" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1 -IpList 1.2.3.4,5.6.7.8" -ForegroundColor Yellow
    exit 3
}

if ($CheckOnly) {
    Write-Host ""
    Write-Host "（-CheckOnly）此刻可用：$($good -join ', ')；未改 hosts、未推送。" -ForegroundColor Yellow
    exit 0
}

# ---------- 3. 逐个固定并真连一次，连不上就换下一个 ----------
$stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = "$hostsPath.bak-$stamp"
Copy-Item -LiteralPath $hostsPath -Destination $backup -Force
Write-Host "hosts 已备份：$backup" -ForegroundColor Gray

$touched = $false
$done    = $false
try {
    foreach ($ip in $good) {
        Write-Host ""
        Write-Host "尝试 $ip ..." -ForegroundColor Cyan
        # 先把「可能已经动过 hosts」置真，再写：写一半抛错时，finally 才不会误报「未改动」。
        $touched = $true
        Add-Pin $ip

        # 确认「固定已生效」再连。判据见 Test-HostsPin / Test-GithubTcp 上方的说明：
        # 不再拿 DNS 客户端的答案当证据，只认 hosts 文件里的那一行 + 一次真实 443 连接。
        $hasLine = $false
        $tcpOk   = $false
        for ($w = 1; $w -le 6; $w++) {
            $hasLine = Test-HostsPin $ip
            $tcpOk   = $false
            if ($hasLine) { $tcpOk = Test-GithubTcp }
            if ($hasLine -and $tcpOk) { break }
            if ($hasLine) {
                Write-Host "  hosts 已写入 $ip，但连接未能确认，等待 ..." -ForegroundColor DarkGray
            }
            else {
                Write-Host "  hosts 里还没读到 $ip github.com，等待 ..." -ForegroundColor DarkGray
            }
            ipconfig /flushdns | Out-Null
            Start-Sleep -Milliseconds 800
        }
        if ($hasLine -and $tcpOk) {
            Write-Host "  解析已指向 $ip（hosts 已写入，443 可连）" -ForegroundColor Gray
        }
        elseif ($hasLine) {
            Write-Host "  hosts 已写入 $ip，但 443 在 2.5 秒内未连上（可能是链路慢，不一定是解析失败），先试一次（可能仍会失败）" -ForegroundColor DarkYellow
        }
        else {
            Write-Host "  hosts 里未读到 $ip 这一行，先试一次（可能仍会失败）" -ForegroundColor DarkYellow
        }

        # 同一个 IP 最多试 $maxTries 轮：握手成功不等于连上，可能是瞬时的
        $remoteSha = $null
        for ($i = 1; $i -le $maxTries -and -not $remoteSha; $i++) {
            if ($i -gt 1) {
                Write-Host "  第 $i 次重试 ..." -ForegroundColor DarkGray
                Start-Sleep -Seconds 2
            }
            $remoteSha = Get-RemoteSha
        }

        if (-not $remoteSha) {
            Write-Host "  该 IP 连不上，换下一个" -ForegroundColor DarkYellow
            Undo-Pin $backup
            continue
        }

        Write-Host "  远端在 $($remoteSha.Substring(0,7))" -ForegroundColor Gray
        if ($remoteSha -eq $targetSha) {
            Write-Host "远端已与本地一致，无需推送。" -ForegroundColor Green
            $done = $true
            break
        }

        Invoke-Push
        $after = Get-RemoteSha
        if ($after -ne $targetSha) {
            throw "推送后复核不一致：远端 $after，$targetLabel $targetSha"
        }
        Write-Host "已推送，远端 = $($after.Substring(0,7))" -ForegroundColor Green
        $done = $true
        break
    }

    if (-not $done) {
        throw "所有可用 IP 都连不上（TLS 握手通过但 git 连接失败），建议换网络：手机热点最省事"
    }
}
finally {
    # 三种状态各说各的：没动过 / 改过已还原 / 还原失败（失败要响亮，不吞异常）
    if (-not $touched) {
        Write-Host "hosts 未改动。" -ForegroundColor Gray
    }
    else {
        try {
            Undo-Pin $backup
        }
        catch {
            Write-Host "⚠ hosts 还原失败：$($_.Exception.Message)" -ForegroundColor Red
            Write-Host "  请手工还原：copy `"$backup`" `"$hostsPath`"" -ForegroundColor Red
            throw
        }
        $left = Get-Content -LiteralPath $hostsPath -Raw
        if ($left -match [regex]::Escape("github.com")) {
            Write-Host "⚠ hosts 还原后仍含 github.com 映射，请手工检查 $hostsPath" -ForegroundColor Red
        }
        else {
            Write-Host "hosts 已还原（备份 $backup 可删）" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "完成：$remote/$refRemote = $short（$whatToPush）" -ForegroundColor Green
if ($Tag) {
    Write-Host "注意：只推送了这一个标签，没有创建 GitHub Release（Release 在网页里手工发）。" -ForegroundColor Gray
}
Write-Host "GitHub：https://github.com/Meta-consciousness-AI/Mcai-agent" -ForegroundColor Gray
