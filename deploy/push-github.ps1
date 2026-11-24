# 推送到 GitHub 的 main 分支。
#
# 为什么需要这个脚本：本机 DNS 常态把 github.com 解析到被封 IP（57.155.223.240），
# 直连必然失败（Recv failure: Connection was reset / Empty reply from server）。
# 2026-11-25 实测：六个候选 IP 里只有 20.233.83.145 能完成 TLS 握手。
# 所以流程是：先试直连 → 不通则测哪个 IP 能握手 → 临时固定到 hosts → 推 → finally 里撤销。
#
# 用法（改 hosts 需要管理员）：
#   powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1
#   powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1 -CheckOnly    # 只诊断，不动任何东西
#
# 注意：
#   1. 不加 --force。非快进会被 Git 拒绝，遇到就停下查分叉原因；
#   2. hosts 用「备份→改→还原」而不是「删掉那一行」，保证不会误伤文件里其他条目；
#   3. 撤销放在 finally，push 失败或抛异常也会还原。

[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [string[]]$IpList
)

$ErrorActionPreference = "Stop"

$root     = Split-Path $PSScriptRoot -Parent
$remote   = "origin"
$branch   = "main"
$hostsPath = Join-Path $env:WINDIR "System32\drivers\etc\hosts"

# 候选 IP：2026-11-25 实测能握手的排在第一位，其余为已知 GitHub 边缘地址
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

# 用 curl 强制指定 IP 完成一次 TLS 握手；只有返回 200 才算这个 IP 可用
# （TCP 能连不算数：今天就是 TCP 通、TLS 被重置）
function Test-Tls([string]$ip) {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $out = & $curl -sS -o NUL -w "%{http_code}" --max-time 8 --resolve "github.com:443:$ip" https://github.com/ 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -eq 0 -and "$out".Trim() -eq "200") { return $true }
    return $false
}

function Get-RemoteSha {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $out = & $git -C $root ls-remote $remote "refs/heads/$branch" 2>$null
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0 -or -not $out) { return $null }
    return ("$out".Trim() -split "\s+")[0]
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

$git  = Find-Git
$curl = Find-Curl

$localSha = (& $git -C $root rev-parse HEAD).Trim()
Write-Host "本机 HEAD：$($localSha.Substring(0,7))" -ForegroundColor Gray
Write-Host "远端 $remote/refs/heads/$branch" -ForegroundColor Gray

# ---------- 第一步：直连能不能用 ----------
$remoteSha = Get-RemoteSha
$direct = ($null -ne $remoteSha)

if ($direct) {
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

Write-Host "直连失败（DNS 解析到被封 IP），开始逐个测候选 IP 的 TLS ..." -ForegroundColor Yellow

# ---------- 第二步：找能握手的 IP ----------
$useIp = $null
foreach ($ip in $candidates) {
    if (Test-Tls $ip) {
        Write-Host "  $ip  可用" -ForegroundColor Green
        $useIp = $ip
        break
    }
    Write-Host "  $ip  不可用" -ForegroundColor DarkGray
}

if (-not $useIp) {
    Write-Host ""
    Write-Host "没有任何候选 IP 能完成 TLS 握手。" -ForegroundColor Red
    Write-Host "按顺序试：① 手机热点；② 你有代理则设 git http.proxy；③ 换一批候选 IP：" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1 -IpList 1.2.3.4,5.6.7.8" -ForegroundColor Yellow
    exit 3
}

if ($CheckOnly) {
    Write-Host ""
    Write-Host "（-CheckOnly）可用 IP：$useIp；未改 hosts、未推送。" -ForegroundColor Yellow
    exit 0
}

# ---------- 第三步：临时固定 IP，推完必须还原 ----------
if (-not (Test-Elevated)) {
    Write-Host ""
    Write-Host "改 hosts 需要管理员权限。请用管理员 PowerShell 重跑：" -ForegroundColor Red
    Write-Host "  powershell -ExecutionPolicy Bypass -File deploy\push-github.ps1" -ForegroundColor Yellow
    exit 2
}

$stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = "$hostsPath.bak-$stamp"
Copy-Item -LiteralPath $hostsPath -Destination $backup -Force
Write-Host "hosts 已备份到 $backup" -ForegroundColor Gray

$pinned = $false
try {
    Add-Content -LiteralPath $hostsPath -Value "$useIp github.com" -Encoding ASCII
    $pinned = $true
    ipconfig /flushdns | Out-Null
    Write-Host "已把 github.com 固定到 $useIp" -ForegroundColor Cyan

    $remoteSha = Get-RemoteSha
    if ($null -eq $remoteSha) { throw "固定 IP 后仍取不到远端分支，放弃" }
    Write-Host "远端在 $($remoteSha.Substring(0,7))" -ForegroundColor Gray

    if ($remoteSha -eq $localSha) {
        Write-Host "远端已与本机一致，无需推送。" -ForegroundColor Green
    }
    else {
        Invoke-Push
        $after = Get-RemoteSha
        if ($after -ne $localSha) {
            throw "推送后复核不一致：远端 $after，本机 $localSha"
        }
        Write-Host "已推送，远端 = $($after.Substring(0,7))" -ForegroundColor Green
    }
}
finally {
    if ($pinned) {
        Copy-Item -LiteralPath $backup -Destination $hostsPath -Force
        ipconfig /flushdns | Out-Null
        if ((Get-Content -LiteralPath $hostsPath -Raw) -match [regex]::Escape($useIp)) {
            Write-Host "⚠ hosts 还原异常：文件里仍有 $useIp，请手工检查 $hostsPath" -ForegroundColor Red
        }
        else {
            Write-Host "hosts 已还原（备份保留在 $backup，可删）" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "完成：$remote/refs/heads/$branch = $($localSha.Substring(0,7))" -ForegroundColor Green
Write-Host "GitHub：https://github.com/Meta-consciousness-AI/Mcai-agent" -ForegroundColor Gray
