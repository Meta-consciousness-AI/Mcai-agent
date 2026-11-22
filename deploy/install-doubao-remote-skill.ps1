# 把 mcai-knowledge-remote 远程技能安装到豆包「用户技能」目录
# 说明：豆包当前只识别已有的 mca-knowledge 技能名，因此安装时沿用该名字，
#       只替换其内容为远程版；旧内容会先备份。
# 用法：.\deploy\install-doubao-remote-skill.ps1
# 卸载：.\deploy\install-doubao-remote-skill.ps1 -Remove

param(
    [switch]$Remove,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$source = Join-Path (Split-Path $PSScriptRoot -Parent) "skills\mcai-knowledge-remote"
$skillsRoot = Join-Path $env:LOCALAPPDATA "Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills"
$target = Join-Path $skillsRoot "mca-knowledge"

if ($Remove) {
    if (Test-Path $target) {
        Remove-Item $target -Recurse -Force
        Write-Host "已移除技能 mca-knowledge。重启豆包后生效。"
    } else {
        Write-Host "未安装。"
    }
    exit 0
}

if (-not (Test-Path $source)) {
    Write-Host "找不到技能源目录：$source" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $skillsRoot)) {
    Write-Host "没找到豆包技能目录：$skillsRoot" -ForegroundColor Yellow
    Write-Host "请先确认豆包已安装并至少启动过一次（智能体模式）。"
    exit 1
}

if ($DryRun) {
    Write-Host "将用远程版覆盖：$target"
    Write-Host "源目录：$source"
    exit 0
}

if (Test-Path $target) {
    $backup = "$target.bak-" + (Get-Date -Format "yyyyMMddHHmmss")
    Rename-Item $target $backup
    Write-Host "旧版本已备份：$backup"
}

Copy-Item $source $target -Recurse -Force

# 豆包按原技能名加载，保留 mca-knowledge 作为显示名
$skillFile = Join-Path $target "SKILL.md"
if (Test-Path $skillFile) {
    $text = [System.IO.File]::ReadAllText($skillFile, [System.Text.Encoding]::UTF8)
    $text = [regex]::Replace($text, "(?m)^name:\s*.*$", "name: mca-knowledge")
    [System.IO.File]::WriteAllText($skillFile, $text, (New-Object System.Text.UTF8Encoding($false)))
}

# 清理之前装过、但豆包未识别的新名字目录，避免混淆
$oldNewName = Join-Path $skillsRoot "mcai-knowledge-remote"
if (Test-Path $oldNewName) {
    $backup = "$oldNewName.bak-" + (Get-Date -Format "yyyyMMddHHmmss")
    Rename-Item $oldNewName $backup
    Write-Host "已停用未识别的新名字目录：$backup"
}

Write-Host "已安装远程版到：$target" -ForegroundColor Green
Write-Host ""
Write-Host "下一步："
Write-Host "  1. 完全退出豆包（右下角托盘图标 → 退出），再重新打开"
Write-Host "  2. 打开「工作」模式，技能列表里应仍有 mca-knowledge"
Write-Host "  3. 新对话里问「什么是元识」，它应直接调用远程接口"
Write-Host ""
Write-Host "卸载：.\deploy\install-doubao-remote-skill.ps1 -Remove"
