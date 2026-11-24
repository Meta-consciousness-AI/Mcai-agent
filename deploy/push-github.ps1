# 推送到 GitHub 的 main 分支。
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
#
# 约束：
#   1. 不加 --force。非快进会被 Git 拒绝，遇到就停下查分叉原因；
#   2. hosts 用「备份→改→还原」而不是「删那一行」，保证不误伤文件里其他条目；
#   3. 还原放在 finally，push 失败或抛异常也会还原；
#   4. 本文件必须存成 UTF-8 带 BOM，否则 Windows PowerShell 5.1 按 GBK 读、中文注释变乱码、报「缺少引号」。

[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [string[]]$IpList
)

$ErrorActionPreference = "Stop"

$root      = Split-Path $PSScriptRoot -Parent
$remote    = "origin"
$branch    = "main"
$hostsPath = Join-Path $env:WINDIR "System32\drivers\etc\hosts"
$maxTries  = 3

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

# 取远端分支 sha；失败时把 git 原话打出来，不吞错
function Get-RemoteSha {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $out = & $git -C $root ls-remote $remote "refs/heads/$branch" 2>&1
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

function Invoke-Push {
    Write-Host "推送到 $remote（$branch）..." -ForegroundColor Cyan
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $git -C $root push $remote $branch
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0) {
        throw "推送失败（凭据问题，或非快进被拒；本脚本不 force，不会覆盖远端历史）"
    }
}

function Add-Pin([string]$ip) {
    Add-Content -LiteralPath $hostsPath -Value "$ip github.com" -Encoding ASCII
    ipconfig /flushdns | Out-Null
}

function Undo-Pin([string]$backup) {
    Copy-Item -LiteralPath $backup -Destination $hostsPath -Force
    ipconfig /flushdns | Out-Null
}

$git  = Find-Git
$curl = Find-Curl
$localSha = (& $git -C $root rev-parse HEAD).Trim()
$short = $localSha.Substring(0, 7)

Write-Host "本机 HEAD：$short" -ForegroundColor Gray
Write-Host "远端：$remote/refs/heads/$branch" -ForegroundColor Gray

# ---------- 0. 权限前置检查（改 hosts 必需），-CheckOnly 不检查 ----------
if (-not $CheckOnly -and -not (Test-Elevated)) {
    Write-Host ""
    Write-Host "改 hosts 需要管理员权限。请用管理员 PowerShell 重跑：" -ForegroundColor Red
    Write-Host "  powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1" -ForegroundColor Yellow
    Write-Host "（只想看哪个 IP 能用，普通窗口加 -CheckOnly 即可）" -ForegroundColor Gray
    exit 2
}

# ---------- 1. 直连能不能用 ----------
Write-Host "试直连 ..." -ForegroundColor Gray
$remoteSha = Get-RemoteSha

if ($remoteSha) {
    Write-Host "直连可用，远端在 $($remoteSha.Substring(0,7))" -ForegroundColor Green
    if ($remoteSha -eq $localSha) {
        Write-Host "远端已与本机一致，无需推送。" -ForegroundColor Green
        exit 0
    }
    if ($CheckOnly) {
        Write-Host "（-CheckOnly）直连可用，可正常推送。" -ForegroundColor Yellow
        exit 0
    }
    Invoke-Push
    $after = Get-RemoteSha
    if ($after -eq $localSha) {
        Write-Host "已推送，远端 = $($after.Substring(0,7))" -ForegroundColor Green
        exit 0
    }
    throw "推送后复核不一致：远端 $after，本机 $localSha"
}

# ---------- 2. 直连不通：先筛出此刻能握手的 IP ----------
Write-Host "直连不通，开始筛候选 IP 的 TLS ..." -ForegroundColor Yellow
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

$pinned = $false
$done   = $false
try {
    foreach ($ip in $good) {
        Write-Host ""
        Write-Host "尝试 $ip ..." -ForegroundColor Cyan
        Add-Pin $ip
        $pinned = $true

        # 等解析真正生效再连：hosts 改完不是立刻生效的（2026-11-25 实测第一轮仍解析到旧 IP，
        # 白等一次 21 秒超时，靠第 2 次重试才成）。这里先确认解析已指向该 IP。
        $resolved = ""
        for ($w = 1; $w -le 6; $w++) {
            $resolved = (Resolve-DnsName github.com -Type A -ErrorAction SilentlyContinue |
                         Where-Object { $_.IPAddress } | Select-Object -ExpandProperty IPAddress) -join ", "
            if ($resolved -match [regex]::Escape($ip)) { break }
            Write-Host "  解析尚未生效（$resolved），等待 ..." -ForegroundColor DarkGray
            ipconfig /flushdns | Out-Null
            Start-Sleep -Milliseconds 800
        }
        if ($resolved -match [regex]::Escape($ip)) {
            Write-Host "  解析已指向 $ip" -ForegroundColor Gray
        }
        else {
            Write-Host "  解析仍为 $resolved，先试一次（可能仍会失败）" -ForegroundColor DarkYellow
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
            $pinned = $false
            continue
        }

        Write-Host "  远端在 $($remoteSha.Substring(0,7))" -ForegroundColor Gray
        if ($remoteSha -eq $localSha) {
            Write-Host "远端已与本机一致，无需推送。" -ForegroundColor Green
            $done = $true
            break
        }

        Invoke-Push
        $after = Get-RemoteSha
        if ($after -ne $localSha) {
            throw "推送后复核不一致：远端 $after，本机 $localSha"
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
    if ($pinned) {
        Undo-Pin $backup
        $left = Get-Content -LiteralPath $hostsPath -Raw
        if ($left -match [regex]::Escape("github.com")) {
            Write-Host "⚠ hosts 还原后仍含 github.com 映射，请手工检查 $hostsPath" -ForegroundColor Red
        }
        else {
            Write-Host "hosts 已还原（备份 $backup 可删）" -ForegroundColor Green
        }
    }
    else {
        Write-Host "hosts 未改动。" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "完成：$remote/refs/heads/$branch = $short" -ForegroundColor Green
Write-Host "GitHub：https://github.com/Meta-consciousness-AI/Mcai-agent" -ForegroundColor Gray
