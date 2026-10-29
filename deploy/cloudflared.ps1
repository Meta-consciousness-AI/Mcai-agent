# 用 Cloudflare 隧道把本机服务临时暴露到公网
#
# 用法：
#   .\deploy\cloudflared.ps1 -Port 8787
#   .\deploy\cloudflared.ps1 -Port 8787 -Token <你的令牌>
#
# 说明：隧道地址每次重启都会变；电脑关机或关掉窗口，外网就访问不到。

param(
    [int]$Port = 8787,
    [string]$Token = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

function Find-Python {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $bundled = Join-Path $env:USERPROFILE ".dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $bundled) { return $bundled }
    throw "未找到 Python，请先安装 Python 3.10+"
}

$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflared) {
    Write-Host "未找到 cloudflared。" -ForegroundColor Yellow
    Write-Host "安装方式（任选其一）："
    Write-Host "  winget install --id Cloudflare.cloudflared"
    Write-Host "  或从 https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/ 下载"
    exit 1
}

if (-not $Token) {
    $Token = Read-Host "输入访问令牌（直接回车则不启用鉴权，仅建议临时演示）"
}

$python = Find-Python
$listening = $false
try {
    $listening = (Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue)
} catch { $listening = $false }

if (-not $listening) {
    Write-Host "启动服务：127.0.0.1:$Port"
    $args = @("run.py", "serve", "--port", "$Port")
    if ($Token) { $args += @("--token", $Token) }
    Start-Process -FilePath $python -ArgumentList $args -WorkingDirectory $root -WindowStyle Minimized
    Start-Sleep -Seconds 3
}

# 构建一次，确保清单里的地址是新的（首次部署时用）
if (-not (Test-Path "dist\.well-known\mcp.json")) {
    Write-Host "首次构建知识库…"
    & $python run.py build
}

Write-Host ""
Write-Host "启动隧道。下面会打印一个 https://xxxx.trycloudflare.com 地址：" -ForegroundColor Cyan
Write-Host "  1) 复制该地址"
Write-Host "  2) 另开一个窗口执行：mcai set-url <地址>"
Write-Host "  3) 再执行：mcai doctor --url <地址> --token $Token"
Write-Host ""
Write-Host "按 Ctrl+C 关闭隧道（服务仍在后台运行）。"
Write-Host ""

& cloudflared tunnel --url "http://127.0.0.1:$Port"
