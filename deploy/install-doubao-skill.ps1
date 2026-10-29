# 把 mcai-knowledge 技能安装到豆包的「用户技能」目录
# 用法：双击运行，或在 PowerShell 里执行 .\deploy\install-doubao-skill.ps1
# 卸载：.\deploy\install-doubao-skill.ps1 -Remove

param(
    [switch]$Remove,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$source = Join-Path (Split-Path $PSScriptRoot -Parent) "doubao-skill\mcai-knowledge"
$skillsRoot = Join-Path $env:LOCALAPPDATA "Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills"
$target = Join-Path $skillsRoot "mcai-knowledge"

if ($Remove) {
    if (Test-Path $target) {
        Remove-Item $target -Recurse -Force
        Write-Host "已移除技能 mcai-knowledge。重启豆包后生效。"
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
    Write-Host "将复制：$source"
    Write-Host "      到：$target"
    exit 0
}

if (Test-Path $target) {
    $backup = "$target.bak-" + (Get-Date -Format "yyyyMMddHHmmss")
    Rename-Item $target $backup
    Write-Host "旧版本已备份：$backup"
}

Copy-Item $source $target -Recurse -Force
Write-Host "已安装到：$target" -ForegroundColor Green
Write-Host ""
Write-Host "下一步："
Write-Host "  1. 完全退出豆包（右下角托盘图标 → 退出），再重新打开"
Write-Host "  2. 打开「工作」模式，看「插件·技能·伙伴」里是否出现 mcai-knowledge"
Write-Host "  3. 新对话里直接问「什么是元意识学说」，不需要再让它执行命令"
Write-Host ""
Write-Host "卸载：.\deploy\install-doubao-skill.ps1 -Remove"