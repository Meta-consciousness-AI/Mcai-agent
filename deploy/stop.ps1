# 停止占用指定端口的服务
param(
    [int]$Port = 8787
)

$lines = netstat -ano | Select-String ":$Port\s" | Select-String "LISTENING"
if (-not $lines) {
    Write-Host "服务未在运行（端口 $Port 无监听）。"
    exit 0
}

$pids = @()
foreach ($line in $lines) {
    $parts = ($line.ToString().Trim() -split "\s+")
    $pids += [int]$parts[-1]
}
$pids = $pids | Sort-Object -Unique

foreach ($procId in $pids) {
    try {
        $proc = Get-Process -Id $procId -ErrorAction Stop
        Write-Host "停止进程 PID $procId（$($proc.ProcessName)）"
        Stop-Process -Id $procId -Force
    } catch {
        Write-Host "无法停止 PID ${procId}：$($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Start-Sleep -Seconds 1
$still = netstat -ano | Select-String ":$Port\s" | Select-String "LISTENING"
if ($still) {
    Write-Host "端口 $Port 仍在监听，可能被其他程序占用。" -ForegroundColor Yellow
    exit 1
}
Write-Host "已停止。"
