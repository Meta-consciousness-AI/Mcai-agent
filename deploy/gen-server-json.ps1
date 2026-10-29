# 用 GitHub 用户名填充 server.json（MCP 注册表要求 io.github.<user>/<server> 命名）
# 用法：.\deploy\gen-server-json.ps1 -GitHubUser yourname
# 预览：.\deploy\gen-server-json.ps1 -GitHubUser yourname -DryRun

param(
    [Parameter(Mandatory = $true)][string]$GitHubUser,
    [string]$Repo = "mcai-agent",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$serverPath = Join-Path $root "server.json"
$pyproject = Join-Path $root "pyproject.toml"

if (-not (Test-Path $serverPath)) { throw "找不到 server.json" }
$match = Select-String -Path $pyproject -Pattern '^version\s*=\s*"([^"]+)"' | Select-Object -First 1
if (-not $match) { throw "无法从 pyproject.toml 读取版本号" }
$version = $match.Matches[0].Groups[1].Value

$data = Get-Content $serverPath -Raw -Encoding UTF8 | ConvertFrom-Json
$data.name = "io.github.$GitHubUser/mcai-knowledge"
$data.repository.url = "https://github.com/$GitHubUser/$Repo"
$data.repository.source = "github"
$data.version = $version
$data.packages[0].version = $version
# 不再写 _meta.note（新 schema 可不带 _meta）

$json = $data | ConvertTo-Json -Depth 12
if ($DryRun) {
    Write-Host $json
    exit 0
}

[System.IO.File]::WriteAllText($serverPath, $json + "`n", (New-Object System.Text.UTF8Encoding($false)))
Write-Host "已更新 server.json：" -ForegroundColor Green
Write-Host "  name: $($data.name)"
Write-Host "  repo: $($data.repository.url)"
Write-Host "  version: $version"
Write-Host ""
Write-Host "下一步：mcp-publisher validate server.json"
