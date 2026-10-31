# 把当前仓库强制推送到 Gitee（使用剪贴板里的私人令牌）
# 用法：双击 推送Gitee.cmd
$ErrorActionPreference = "Stop"

$root = Split-Path $PSScriptRoot -Parent
$user = "Meta-consciousness-AI"
$repo = "Mcai-agent"

function Find-Git {
    $cmd = Get-Command git -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($p in @("C:\Program Files\Git\cmd\git.exe", "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe")) {
        if (Test-Path $p) { return $p }
    }
    throw "找不到 git"
}
$git = Find-Git

$token = (Get-Clipboard -Raw).Trim()
if (-not $token) { throw "剪贴板为空：请先复制 Gitee 私人令牌" }
if ($token.Length -lt 16) { throw "令牌长度异常，请确认复制的是完整令牌" }

$remote = "https://oauth2:$token@gitee.com/$user/$repo.git"
Write-Host "推送到 Gitee：$user/$repo ..." -ForegroundColor Cyan
$prev = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $git -C $root push --force $remote main
$code = $LASTEXITCODE
$ErrorActionPreference = $prev

if ($code -ne 0) { throw "推送失败（令牌权限或仓库地址有误）" }

Write-Host ""
Write-Host "✅ 已推送到 Gitee" -ForegroundColor Green
Write-Host "仓库：https://gitee.com/$user/$repo"
Write-Host "下一步：在云托管里用「公开仓库」填这个地址，分支 main。"
