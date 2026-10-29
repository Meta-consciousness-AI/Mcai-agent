# 把 dist/ 发布到 <用户名>.github.io 仓库（GitHub Pages 根路径站点）
# 用法：双击 发布官网.cmd
# 前置：已在 GitHub 新建空仓库 Meta-consciousness-AI.github.io

param(
    [string]$User = "Meta-consciousness-AI",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
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

if ($DryRun) {
    Write-Host "DryRun：将把 $dist 发布到 https://github.com/$User/$User.github.io.git" -ForegroundColor Yellow
    Write-Host "站点地址：https://$($User.ToLower()).github.io/"
    exit 0
}

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

@'
✅ 官网已发布

地址（首次需 1–2 分钟生效）：
  https://meta-consciousness-ai.github.io/

下一步：
  1. 打开仓库 Settings → Pages，确认 Source 是 Deploy from a branch / main / (root)
  2. 等 Actions 或 Pages 显示 Published
  3. 再提交 sitemap 到 Google / Bing
'@ | Write-Host
