# 登录 MCP 注册表并发布 server.json
# 用法：双击 上架MCP.cmd

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

$exe = Join-Path $PSScriptRoot "bin\mcp-publisher.exe"
if (-not (Test-Path $exe)) {
    Write-Host "没有找到 mcp-publisher.exe，请先双击 安装mcp-publisher.cmd" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path "server.json")) {
    Write-Host "没有找到 server.json" -ForegroundColor Red
    exit 1
}

Write-Host "第 1 步：登录 GitHub（会显示一个设备代码）" -ForegroundColor Cyan
Write-Host ""

# 凭据存到项目目录，避开用户主目录的写入限制
$homeDir = Join-Path $PSScriptRoot "mcp-home"
New-Item -ItemType Directory -Force -Path $homeDir | Out-Null
$env:USERPROFILE = $homeDir
$env:HOME = $homeDir

& $exe login github
if ($LASTEXITCODE -ne 0) {
    Write-Host "登录失败，请重试。" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "第 2 步：提交到 MCP 注册表" -ForegroundColor Cyan
Write-Host ""
& $exe publish
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "发布失败。常见原因：" -ForegroundColor Yellow
    Write-Host "  - PyPI 上的 README 没有 mcp-name 标记"
    Write-Host "  - server.json 的 name 与 GitHub 用户名不一致"
    Write-Host "  - 版本号在注册表里已存在"
    exit 1
}

Write-Host ""
Write-Host "✅ 已提交到 MCP 注册表" -ForegroundColor Green
Write-Host "查询：https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.Meta-consciousness-AI/mcai-knowledge"
