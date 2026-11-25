# 把当前仓库推送到 Gitee 的 master 分支。
#
# 令牌来源（按优先级）：
#   1. 凭据库：E:\th\元意识\元意识运营\Mcai-Agent\mcai-knowledge\Gitee令牌.txt
#      （2026-11-25 定的唯一凭据位置，见 docs/工作原则.md「凭据存放处」）
#   2. 剪贴板（仅当凭据库没有时）
#   两处都没有就报错，不提供交互式输入框——Read-Host -AsSecureString 在这个 console 里
#   粘贴不完整（2026-11-25 两次都只拿到不足 16 个字符），不作为入口。
#
# 约束：
#   1. 不加 --force。非快进会被 Git 拒绝，遇到就停下查分叉原因；Gitee 用 master，推 main:master。
#   2. 令牌只允许在内存与请求里：任何输出（尤其是 git 原话）打印前都要过 Hide-Token。
#   3. 推送后用 ls-remote 复核远端 master 的 sha 是否等于本机 HEAD，不一致就报错退出。
#   4. 本文件必须存成 UTF-8 带 BOM，否则 Windows PowerShell 5.1 按 GBK 读、中文注释变乱码、报「缺少引号」。
$ErrorActionPreference = "Stop"

$root     = Split-Path $PSScriptRoot -Parent
$user     = "Meta-consciousness-AI"
$repo     = "Mcai-agent"
$credFile = "E:\th\元意识\元意识运营\Mcai-Agent\mcai-knowledge\Gitee令牌.txt"
$branch   = "main:master"

function Find-Git {
    $cmd = Get-Command git -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($p in @("C:\Program Files\Git\cmd\git.exe", "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe")) {
        if (Test-Path $p) { return $p }
    }
    throw "找不到 git"
}

function Get-TokenFromStore {
    if (-not (Test-Path -LiteralPath $credFile)) { return "" }
    try {
        $raw = Get-Content -LiteralPath $credFile -Raw -ErrorAction Stop
        if ($null -eq $raw) { return "" }
        return ([string]$raw).Trim()
    }
    catch { return "" }
}

function Get-TokenFromClipboard {
    try {
        $raw = Get-Clipboard -Raw
        if ($null -eq $raw) { return "" }
        return ([string]$raw).Trim()
    }
    catch { return "" }
}

# 令牌脱敏：任何要打印的文本都先过这里。既换 oauth2:<token> 段，也换孤立的令牌串。
function Hide-Token([string]$text) {
    if ($null -eq $text) { return "" }
    $out = [string]$text
    if ($script:token) {
        $out = $out.Replace("oauth2:$($script:token)", "oauth2:***")
        $out = $out.Replace($script:token, "***")
    }
    return $out
}

# 取远端 master 的 sha；失败时打印 git 原话（已脱敏），不吞错。
function Get-RemoteSha {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $out = & $git -C $root ls-remote $remote "refs/heads/master" 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0) {
        Write-Host "    git ls-remote 失败：" -ForegroundColor DarkYellow
        (@($out) | ForEach-Object { "$_" } | Select-Object -First 8) | ForEach-Object { Write-Host ("      " + (Hide-Token $_)) -ForegroundColor DarkYellow }
        return $null
    }
    $line = ("$out" -split "`n" | Where-Object { $_ -match "^[0-9a-f]{40}\s" } | Select-Object -First 1)
    if (-not $line) { return $null }
    return ($line.Trim() -split "\s+")[0]
}

function Invoke-Push {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $out = & $git -C $root push $remote $branch 2>&1
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -eq 0) { return }
    $lines = @($out | ForEach-Object { "$_" })
    Write-Host "git 原话：" -ForegroundColor DarkYellow
    $lines | Select-Object -First 12 | ForEach-Object { Write-Host ("  " + (Hide-Token $_)) -ForegroundColor DarkYellow }
    if ($lines.Count -gt 12) {
        Write-Host ("  …（共 " + $lines.Count + " 行，只显示前 12 行）") -ForegroundColor DarkYellow
    }
    throw "推送失败（令牌权限、仓库地址有误，或非快进被拒；本脚本不 force，不会覆盖远端历史）"
}

# ---------- 1. 取令牌：先凭据库，后剪贴板 ----------
$token  = Get-TokenFromStore
$source = "凭据库"
if (-not $token) {
    $token  = Get-TokenFromClipboard
    $source = "剪贴板"
}
if (-not $token) {
    throw "没有拿到令牌。令牌请放进凭据库（$credFile）或复制到剪贴板。"
}
$script:token = $token

# ---------- 2. 校验形状：Gitee 私人令牌是 32 位十六进制 ----------
$shapeOk   = ($token -match '^[0-9a-fA-F]{32}$')
$shapeText = "不对"
if ($shapeOk) { $shapeText = "OK" }
Write-Host "令牌来源：$source  len=$($token.Length) shape=$shapeText" -ForegroundColor Gray
if (-not $shapeOk) {
    throw "这不像令牌（Gitee 私人令牌应为 32 位十六进制）。可能是剪贴板里放的是别的内容；已停止，未连接远端。"
}

# ---------- 3. 推送 ----------
$git    = Find-Git
$remote = "https://oauth2:$token@gitee.com/$user/$repo.git"
Write-Host "推送到 Gitee：$user/$repo ..." -ForegroundColor Cyan
Invoke-Push

# ---------- 4. 推送后复核：远端 master 必须等于本机 HEAD ----------
$localSha = (& $git -C $root rev-parse HEAD).Trim()
$after    = Get-RemoteSha
if (-not $after) {
    throw "推送后复核失败：读不到远端 master 的 sha（见上）"
}
if ($after -ne $localSha) {
    throw "推送后复核不一致：远端 $after，本机 $localSha"
}

Write-Host ""
Write-Host "✅ 已推送到 Gitee，远端 master = $($after.Substring(0,7))（与本机一致）" -ForegroundColor Green
Write-Host "仓库：https://gitee.com/$user/$repo"
Write-Host "下一步：在云托管里用「公开仓库」填这个地址，分支 master。"
