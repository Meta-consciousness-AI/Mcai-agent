# 对话模式辅助：把剪贴板里的问题发给本机知识库，把「资料 + 问题」放回剪贴板
# 用法：复制你的问题 → 双击「对话模式查询.cmd」→ 到豆包对话框粘贴发送
# 也可直接指定问题（便于测试）：.\clipboard-query.ps1 -Question "什么是元意识" -DryRun

param(
    [string]$Question = "",
    [string]$BaseUrl = "http://127.0.0.1:8787",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if (-not $Question) {
    $Question = (Get-Clipboard -Raw -ErrorAction SilentlyContinue)
}
if (-not $Question -or -not $Question.Trim()) {
    Write-Host "剪贴板是空的：请先复制你的问题。" -ForegroundColor Yellow
    exit 1
}
$Question = $Question.Trim()

try {
    $body = @{ question = $Question } | ConvertTo-Json -Compress
    $resp = Invoke-RestMethod -Uri "$BaseUrl/api/v1/answer" -Method Post `
        -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 15
} catch {
    Write-Host "调用失败：$($_.Exception.Message)" -ForegroundColor Red
    Write-Host "本机知识库可能未启动，请双击项目目录下的 启动.cmd" -ForegroundColor Yellow
    exit 1
}

if ($resp.type -eq "policy") {
    $payload = $resp.answer
} elseif ($resp.type -eq "none") {
    $payload = "（知识库未收录该问题，请如实说明，不要编造。）`n`n问题：$Question"
} else {
    $refs = @()
    if ($resp.citations) {
        foreach ($c in $resp.citations | Select-Object -First 2) {
            $refs += "- 《$($c.doc)》$($c.section)：$($c.quote)"
        }
    }
    $payload = "请严格依据下面这份来自「元意识学说」知识库的资料回答问题，保留出处，不要自行改写术语。`n`n【资料】`n$($resp.context)`n`n【出处】`n$($refs -join "`n")`n`n【问题】`n$Question"
}

if ($DryRun) {
    Write-Host "--- 将要复制的内容 ---"
    Write-Host $payload
    exit 0
}

Set-Clipboard -Value $payload
Write-Host "已复制到剪贴板（类型：$($resp.type)）。" -ForegroundColor Green
Write-Host "现在切到豆包对话模式，粘贴并发送即可。"
