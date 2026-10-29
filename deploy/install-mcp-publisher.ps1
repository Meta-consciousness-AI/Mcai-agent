# 下载 mcp-publisher 到 deploy\bin
# 用法：双击 安装mcp-publisher.cmd

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$bin = Join-Path $PSScriptRoot "bin"
New-Item -ItemType Directory -Force -Path $bin | Out-Null
$exe = Join-Path $bin "mcp-publisher.exe"

if (Test-Path $exe) {
    Write-Host "已存在：$exe" -ForegroundColor Green
    & $exe --help 2>&1 | Select-Object -First 3
    exit 0
}

$arch = if ([System.Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture -eq "Arm64") { "arm64" } else { "amd64" }
$asset = "mcp-publisher_windows_$arch.tar.gz"
$urls = @(
    "https://github.com/modelcontextprotocol/registry/releases/latest/download/$asset",
    "https://gh-proxy.com/https://github.com/modelcontextprotocol/registry/releases/latest/download/$asset",
    "https://ghfast.top/https://github.com/modelcontextprotocol/registry/releases/latest/download/$asset"
)

$tar = Join-Path $bin $asset
$ok = $false
foreach ($u in $urls) {
    Write-Host "尝试下载：$u" -ForegroundColor Cyan
    try {
        $ProgressPreference = "SilentlyContinue"
        & curl.exe -L --ssl-no-revoke --retry 2 --connect-timeout 30 -o $tar $u
        if ((Test-Path $tar) -and ((Get-Item $tar).Length -gt 1MB)) { $ok = $true; break }
    } catch {
        Write-Host "失败：$($_.Exception.Message)" -ForegroundColor Yellow
    }
}
if (-not $ok) {
    Write-Host "下载失败。可以手动下载后放到：$bin" -ForegroundColor Red
    Write-Host "地址：$($urls[0])"
    exit 1
}

Write-Host "解压..." -ForegroundColor Cyan
Push-Location $bin
try {
    & tar.exe -xzf $tar mcp-publisher.exe
} finally {
    Pop-Location
}
Remove-Item $tar -Force -ErrorAction SilentlyContinue

if (-not (Test-Path $exe)) {
    Write-Host "解压后没有找到 mcp-publisher.exe，请检查压缩包内容。" -ForegroundColor Red
    exit 1
}
Write-Host "已安装：$exe" -ForegroundColor Green
& $exe --help 2>&1 | Select-Object -First 5
