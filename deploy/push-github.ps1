# 把项目推送到 GitHub
# 前置：已在 GitHub 网页新建空仓库（Public，不要勾选 README）
# 用法：.\deploy\push-github.ps1 -GitHubUser 你的用户名

param(
    [string]$GitHubUser = "",
    [string]$Repo = "mcai-agent",
    [string]$Message = "mcai-knowledge 0.1.0",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

if (-not $GitHubUser) {
    $GitHubUser = (Read-Host "请输入 GitHub 用户名").Trim()
}
if (-not $GitHubUser) { throw "没有提供 GitHub 用户名" }

function Find-Git {
    $cmd = Get-Command git -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($p in @("C:\Program Files\Git\cmd\git.exe", "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe")) {
        if (Test-Path $p) { return $p }
    }
    throw "找不到 git，请先安装 Git for Windows"
}

$git = Find-Git

if ($DryRun) {
    Write-Host "DryRun：将把项目推送到 https://github.com/$GitHubUser/$Repo.git" -ForegroundColor Yellow
    Write-Host "（未执行 init / add / commit / push）"
    exit 0
}

# 初始化（先 init，check-ignore 才能工作）
if (-not (Test-Path ".git")) {
    Write-Host "初始化仓库..." -ForegroundColor Cyan
    & $git init -b main
}

# 防呆：确认敏感文件被忽略
$mustIgnore = @("config/corpus.json", "config/llm.json", "data/token.txt")
foreach ($p in $mustIgnore) {
    if (Test-Path $p) {
        & $git check-ignore -q $p
        if ($LASTEXITCODE -ne 0) {
            throw "$p 没有被 .gitignore 排除，停止推送。请检查 .gitignore。"
        }
    }
}
if (Test-Path "data") {
    & $git check-ignore -q "data/access.log" 2>$null
    if ($LASTEXITCODE -ne 0) { throw "data/ 没有被忽略，停止推送。" }
}

# 提交
$ErrorActionPreference = "Continue"; & $git add .; $addCode = $LASTEXITCODE; $ErrorActionPreference = "Stop"
$staged = & $git diff --cached --name-only
if ($staged) {
    Write-Host "提交 $($staged.Count) 个文件..." -ForegroundColor Cyan
    $ErrorActionPreference = "Continue"; & $git -c core.quotepath=false commit -m $Message; $commitCode = $LASTEXITCODE; $ErrorActionPreference = "Stop"
} else {
    Write-Host "没有新改动需要提交。" -ForegroundColor Yellow
}

# 远端
$remote = ""
try { $remote = (& $git remote get-url origin) 2>$null } catch { $remote = "" }
$url = "https://github.com/$GitHubUser/$Repo.git"
if (-not $remote) {
    Write-Host "添加远端 $url" -ForegroundColor Cyan
    & $git remote add origin $url
} elseif ($remote -ne $url) {
    Write-Host "更新远端：$remote → $url" -ForegroundColor Yellow
    & $git remote set-url origin $url
}

# 推送
Write-Host "推送到 origin main（首次会弹出浏览器登录 GitHub）..." -ForegroundColor Cyan
$ErrorActionPreference = "Continue"; & $git push -u origin main; $pushCode = $LASTEXITCODE; $ErrorActionPreference = "Stop"
if ($pushCode -ne 0) { throw "推送失败：请确认仓库已在 GitHub 创建且为空" }

Write-Host ""
Write-Host "✅ 推送完成" -ForegroundColor Green
Write-Host "仓库：https://github.com/$GitHubUser/$Repo"
Write-Host ""
Write-Host "下一步："
Write-Host "  1. 运行 .\deploy\gen-server-json.ps1 -GitHubUser $GitHubUser"
Write-Host "  2. 安装 mcp-publisher 并提交注册表"
