param(
    [string]$Question = "",
    [string]$Questions = "",
    [string]$BaseUrl = "http://127.0.0.1:8787"
)

$ErrorActionPreference = "Stop"
$ua = "mcai-skill/1.0 (+doubao-skill)"

function Fail($msg) {
    [pscustomobject]@{
        ok    = $false
        error = $msg
        hint  = "本机知识库服务可能未启动：请双击项目目录下的 启动.cmd 后重试"
    } | ConvertTo-Json -Compress
    exit 0
}

# 多个问题用 | 分隔，例如 -Questions "什么是元识|什么是元知"
$list = @()
if ($Questions) {
    $list = $Questions -split '\|' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
}

try {
    if ($list.Count -gt 0) {
        $payload = @{ questions = $list } | ConvertTo-Json -Compress
        $resp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/answer/batch" -Method Post `
            -UserAgent $ua -ContentType "application/json; charset=utf-8" `
            -Body ([System.Text.Encoding]::UTF8.GetBytes($payload)) -TimeoutSec 30
        $resp | ConvertTo-Json -Depth 8
        exit 0
    }

    if (-not $Question) { Fail "缺少 -Question 或 -Questions 参数" }

    $body = @{ question = $Question } | ConvertTo-Json -Compress
    $resp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/answer" -Method Post `
        -UserAgent $ua -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 15
    $resp | ConvertTo-Json -Depth 8
}
catch {
    Fail $_.Exception.Message
}
exit 0