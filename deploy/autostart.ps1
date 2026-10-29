# 注册「自动驾驶」计划任务：每 5 分钟检查一次语料、自动重建、健康自检
# 用法：.\deploy\autostart.ps1 [-Port 8787] [-Home <工作区>] [-EveryMinutes 5]
# 卸载：.\deploy\autostart.ps1 -Remove

param(
    [int]$Port = 8787,
    [string]$Home = "",
    [int]$EveryMinutes = 5,
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent

function Find-Python {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $bundled = Join-Path $env:USERPROFILE ".dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $bundled) { return $bundled }
    throw "未找到 Python，请先安装 Python 3.10+"
}

if ($Remove) {
    schtasks /Delete /TN "MCAI-Autopilot" /F 2>$null | Out-Null
    Write-Host "已移除计划任务 MCAI-Autopilot"
    exit 0
}

$python = Find-Python
$homePath = if ($Home) { (Resolve-Path $Home).Path } else { $root }
$action = "`"$python`" -m mcai autopilot --once --home `"$homePath`" --port $Port"

Write-Host "注册计划任务：每 $EveryMinutes 分钟执行一次"
Write-Host "  解释器：$python"
Write-Host "  工作区：$homePath"
Write-Host "  命令：  $action"

schtasks /Create /TN "MCAI-Autopilot" /SC MINUTE /MO $EveryMinutes /TR $action /F | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "计划任务创建失败（可能需要管理员权限）。" -ForegroundColor Yellow
    Write-Host "可以手动添加：任务计划程序 → 创建任务 → 每 $EveryMinutes 分钟 → 启动程序：$python"
    exit 1
}

Write-Host "已注册。立即执行一次自检…"
& $python -m mcai autopilot --once --home $homePath --port $Port
Write-Host ""
Write-Host "之后每 $EveryMinutes 分钟会自动：检查语料变化 → 需要时重建 → 检查服务是否在线 → 写状态文件。"
Write-Host "查看状态：python -m mcai status --home `"$homePath`""
