# 启动公网隧道（Cloudflare 快速隧道）
# 用法：双击 启动隧道.cmd，或在 PowerShell 里执行本脚本
# 默认用 HTTP/2（部分网络下 QUIC 注册会超时）

param(
    [int]$Port = 8788,
    [string]$Token = "",
    [ValidateSet("http2", "quic", "auto")]
    [string]$Protocol = "http2"
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$bin = Join-Path $PSScriptRoot "bin\cloudflared.exe"
$url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

function Find-Python {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $bundled = "C:\Users\HP\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $bundled) { return $bundled }
    return $null
}

# 1. 令牌
if (-not $Token) {
    $tokenFile = Join-Path $root "data\tunnel-token.txt"
    if (Test-Path $tokenFile) {
        $Token = ((Get-Content $tokenFile -Raw) -replace "^\uFEFF", "").Trim()
    } else {
        $chars = (48..57) + (65..90) + (97..122)
        $Token = -join (1..32 | ForEach-Object { [char]($chars | Get-Random) })
        [System.IO.File]::WriteAllText($tokenFile, $Token, (New-Object System.Text.UTF8Encoding($false)))
    }
}
Write-Host "令牌：$Token" -ForegroundColor Cyan

# 2. cloudflared
if (-not (Test-Path $bin)) {
    Write-Host "未找到 cloudflared，正在下载（约 50 MB）..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path (Split-Path $bin) | Out-Null
    try {
        $ProgressPreference = "SilentlyContinue"
        Invoke-WebRequest -Uri $url -OutFile $bin -UseBasicParsing -TimeoutSec 300
    } catch {
        Write-Host "PowerShell 下载失败，改用 curl..." -ForegroundColor Yellow
        & curl.exe -L --ssl-no-revoke --retry 2 -o $bin $url
    }
    if (-not (Test-Path $bin)) {
        Write-Host "下载失败。请手动下载后放到：$bin" -ForegroundColor Red
        Write-Host "地址：$url"
        exit 1
    }
}
Write-Host "cloudflared: $([math]::Round((Get-Item $bin).Length / 1MB, 1)) MB"

# 3. 起一个带令牌的本地实例
$listening = netstat -ano | Select-String ":$Port\s" | Select-String "LISTENING"
if (-not $listening) {
    $py = Find-Python
    if (-not $py) {
        Write-Host "找不到 python，请在项目目录里用 python -m mcai serve 启动。" -ForegroundColor Red
        exit 1
    }
    Write-Host "启动服务实例（端口 $Port，仅本机）..."
    Start-Process -FilePath $py `
        -ArgumentList @("-m", "mcai", "serve", "--home", $root, "--port", $Port,
                        "--host", "127.0.0.1", "--token", $Token, "--autopilot", "0") `
        -WorkingDirectory $root -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $root "data\tunnel-server.log") `
        -RedirectStandardError (Join-Path $root "data\tunnel-server.err")
    Start-Sleep -Seconds 3
} else {
    Write-Host "端口 $Port 已在监听，复用它（请确认它的令牌与上面一致）。" -ForegroundColor Yellow
}

# 4. 起隧道（默认 HTTP/2）
$log = Join-Path $root "data\tunnel.log"
$err = Join-Path $root "data\tunnel.err"
Remove-Item $log, $err -Force -ErrorAction SilentlyContinue
Write-Host "建立隧道（协议：$Protocol）..."
Start-Process -FilePath $bin `
    -ArgumentList @("tunnel", "--url", "http://127.0.0.1:$Port", "--no-autoupdate",
                    "--protocol", $Protocol, "--edge-ip-version", "4") `
    -WindowStyle Hidden -RedirectStandardOutput $log -RedirectStandardError $err

# 5. 等两件事：拿到地址 + 注册连接（缺一不可）
$public = $null
$registered = $false
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 1000
    foreach ($f in @($log, $err)) {
        if (-not (Test-Path $f)) { continue }
        if (-not $public) {
            $m = Select-String -Path $f -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -ErrorAction SilentlyContinue |
                 Select-Object -First 1
            if ($m) { $public = $m.Matches[0].Value }
        }
        if (-not $registered) {
            $r = Select-String -Path $f -Pattern 'Registered tunnel connection' -ErrorAction SilentlyContinue |
                 Select-Object -First 1
            if ($r) { $registered = $true }
        }
    }
    if ($public -and $registered) { break }
}

if (-not ($public -and $registered)) {
    Write-Host ""
    Write-Host "隧道没有注册成功（Cloudflare 会返回 1033）。" -ForegroundColor Red
    Write-Host "常见原因：QUIC 被网络拦截、公司代理、临时故障。"
    Write-Host "可以换协议重试："
    Write-Host "  powershell -File deploy\start-tunnel.ps1 -Protocol quic"
    Write-Host ""
    if (Test-Path $err) { Get-Content $err -Tail 12 -Encoding UTF8 }
    exit 1
}

Set-Clipboard -Value $public
Write-Host ""
Write-Host "公网地址：$public" -ForegroundColor Green
Write-Host "令牌：    $Token"
Write-Host "健康检查：$public/api/v1/health"
Write-Host ""
Write-Host "示例："
Write-Host "  curl -H `"Authorization: Bearer $Token`" `"$public/api/v1/answer?q=什么是元意识`""
Write-Host ""
Write-Host "已复制地址到剪贴板。关闭隧道：双击 停止隧道.cmd"
