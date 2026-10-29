# 安装元意识知识库（本机）
# 用法：右键「使用 PowerShell 运行」，或在终端执行 .\install.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Find-Python {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $bundled = Join-Path $env:USERPROFILE ".dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $bundled) { return $bundled }
    throw "未找到 Python，请先安装 Python 3.10+"
}

$python = Find-Python
Write-Host "使用解释器：$python"

Write-Host "安装中（pip install -e .）…"
& $python -m pip install -e . --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip 安装失败。可以先用开发模式运行：" -ForegroundColor Yellow
    Write-Host "  python run.py build" -ForegroundColor Yellow
    Write-Host "  python run.py serve --port 8787" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "安装完成。常用命令：" -ForegroundColor Green
Write-Host "  mcai build                 重建知识库、站点、数据集"
Write-Host "  mcai serve --port 8787     启动网页与 HTTP API"
Write-Host "  mcai mcp                   启动 MCP 服务器（给 Claude / Cursor 用）"
Write-Host "  mcai report                体检报告"
Write-Host ""
Write-Host "其他工作区：mcai <命令> --home <目录>；或设置环境变量 MCAI_HOME。"
