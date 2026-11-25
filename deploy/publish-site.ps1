# 【已废弃，2026-11-25】不要再把 dist/ 推到这里。
#
# 为什么废弃：本脚本原来的发布目标是 GitHub Pages 仓库 Meta-consciousness-AI.github.io，
#   2026-11-25 实测 https://meta-consciousness-ai.github.io/ 返回 404——那个站点不存在。
#
# 真实部署方式（线上站点）：腾讯云 CloudBase 静态托管
#   https://mcai-knowledge-d7gtizltz910e2269-1316838521.tcloudbaseapp.com
#   更新靠腾讯云控制台手工上传 dist/；本机没有 tcb / cloudbase CLI，仓库里也没有部署脚本。
#   完整四步见 deploy/README.md「静态站点发布（CloudBase）」。
#
# 现在的行为：不带 -DryRun 运行时只打印这段说明并 exit 1，不会再往任何仓库推东西；
#   -DryRun 仍可用，供以后想复用的人先看清"当年想发到哪"。
#
# 用法：powershell -ExecutionPolicy Bypass -File deploy\publish-site.ps1 -DryRun

param(
    [string]$User = "Meta-consciousness-AI",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if (-not $DryRun) {
    Write-Host ""
    Write-Host "【已废弃】deploy/publish-site.ps1 不再发布任何东西。" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "原因：原发布目标 https://meta-consciousness-ai.github.io/ 2026-11-25 实测 404（没有站点）。"
    Write-Host "线上真实站点是 CloudBase：https://mcai-knowledge-d7gtizltz910e2269-1316838521.tcloudbaseapp.com"
    Write-Host "更新方式：腾讯云控制台手工上传 dist/（无脚本、无 CLI）。"
    Write-Host ""
    Write-Host "完整流程见 deploy/README.md「静态站点发布（CloudBase）」；只看旧目标可用 -DryRun。" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "【已废弃】-DryRun 只做说明，不会推送。" -ForegroundColor Yellow
Write-Host "旧实现本来要发到：https://github.com/$User/$User.github.io.git"
Write-Host "对应站点地址：https://$($User.ToLower()).github.io/ （2026-11-25 实测 404）"
Write-Host "真实站点：https://mcai-knowledge-d7gtizltz910e2269-1316838521.tcloudbaseapp.com"
exit 0

# ---------------------------------------------------------------------------
# 以下为 2026-11-25 之前的旧实现，已不可达（上面已 exit 1 / exit 0），
# 仅保留作参考：它会把 dist/ 复制到 site-publish/，git init 后 --force 推到 GitHub Pages。
# ---------------------------------------------------------------------------
$root = Split-Path $PSScriptRoot -Parent
$dist = Join-Path $root "dist"
$site = Join-Path $root "site-publish"

if (-not (Test-Path (Join-Path $dist "index.html"))) {
    throw "dist/index.html 不存在，请先运行 mcai build"
}

function Find-Git {
    $cmd = Get-Command git -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($p in @("C:\Program Files\Git\cmd\git.exe", "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe")) {
        if (Test-Path $p) { return $p }
    }
    throw "找不到 git"
}
$git = Find-Git

# 重建发布目录
if (Test-Path $site) { Remove-Item $site -Recurse -Force }
New-Item -ItemType Directory -Force -Path $site | Out-Null
Copy-Item (Join-Path $dist "*") $site -Recurse -Force
# GitHub Pages 默认用 Jekyll，加 .nojekyll 避免处理下划线文件
New-Item -ItemType File -Force -Path (Join-Path $site ".nojekyll") | Out-Null

Push-Location $site
try {
    & $git init -b main | Out-Null
    & $git add -A
    & $git -c core.quotepath=false commit -m "publish mcai-knowledge site" | Out-Null
    & $git remote add origin "https://github.com/$User/$User.github.io.git"
    Write-Host "推送到 $User.github.io ..." -ForegroundColor Cyan
    $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    & $git push -u origin main --force
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0) { throw "推送失败：请确认仓库已创建且为空" }
} finally {
    Pop-Location
}
