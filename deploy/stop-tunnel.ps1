# 停止公网隧道和隧道专用实例
$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path $PSScriptRoot -Parent
$bin = Join-Path $PSScriptRoot "bin\cloudflared.exe"

Get-Process cloudflared -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -eq $bin } |
    ForEach-Object { Stop-Process -Id $_.Id -Force; Write-Host "已停止 cloudflared (PID $($_.Id))" }

$lines = netstat -ano | Select-String ':8788\s' | Select-String 'LISTENING'
foreach ($line in $lines) {
    $cols = ($line.Line -split '\s+') | Where-Object { $_ }
    $procId = $cols[-1]
    if ($procId -match '^\d+$') {
        Stop-Process -Id ([int]$procId) -Force
        Write-Host "已停止 8788 上的服务 (PID $procId)"
    }
}

Write-Host "完成。本机 8787 的服务未受影响。"
