# 后台启动服务（隐藏窗口），日志写到 data\server.log
param(
    [int]$Port = 8787
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent

function Find-Python {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $bundled = Join-Path $env:USERPROFILE ".dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $bundled) { return $bundled }
    throw "未找到 Python"
}

# 已在运行则不重复启动
try {
    $existing = Invoke-WebRequest "http://127.0.0.1:$Port/api/v1/health" -UseBasicParsing -TimeoutSec 2
    if ($existing.StatusCode -eq 200) {
        Write-Host "服务已经在运行：http://127.0.0.1:$Port"
        exit 0
    }
} catch { }

$python = Find-Python
$dataDir = Join-Path $root "data"
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

$args = @("-m", "mcai", "serve", "--home", $root, "--port", "$Port", "--autopilot", "300")
Start-Process -FilePath $python -ArgumentList $args -WorkingDirectory $root -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $dataDir "server.log") `
    -RedirectStandardError (Join-Path $dataDir "server.err.log")

Start-Sleep -Seconds 3
try {
    $resp = Invoke-WebRequest "http://127.0.0.1:$Port/api/v1/health" -UseBasicParsing -TimeoutSec 5
    $info = $resp.Content | ConvertFrom-Json
    Write-Host "已启动：http://127.0.0.1:$Port"
    Write-Host "  概念 $($info.concepts) · 问答 $($info.faqs) · 关系 $($info.relations)"
    Write-Host "  日志：data\server.log"
} catch {
    Write-Host "启动失败，请查看 data\server.err.log" -ForegroundColor Red
    exit 1
}
