# 把 wheel 发布到 PyPI（或 TestPyPI）
# 用法：
#   .\deploy\publish-pypi.ps1                 # 发布到正式 PyPI
#   .\deploy\publish-pypi.ps1 -TestPyPI       # 先发到 TestPyPI 演练
#   .\deploy\publish-pypi.ps1 -Token pypi-xxx # 直接给 token（不推荐，会留在历史里）

param(
    [switch]$TestPyPI,
    [string]$Token = "",
    [switch]$SkipBuild,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

function Find-Python {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $bundled = "C:\Users\HP\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $bundled) { return $bundled }
    throw "找不到 python"
}

$py = Find-Python

# 1. 构建
if (-not $SkipBuild) {
    Write-Host "构建 wheel..." -ForegroundColor Cyan
    & $py tools\build_wheel.py
    if ($LASTEXITCODE -ne 0) { throw "构建失败" }
}
$wheel = Get-ChildItem dist_pkg\*.whl | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $wheel) { throw "dist_pkg 里没有 wheel" }
Write-Host "使用：$($wheel.Name)（$([math]::Round($wheel.Length/1KB)) KB）"

$repo = if ($TestPyPI) { "testpypi" } else { "pypi" }
if ($DryRun) {
    Write-Host "DryRun：将上传 $($wheel.Name) 到 $repo（未执行上传）" -ForegroundColor Yellow
    exit 0
}

# 2. 确保 twine（原生命令的 stderr 不能被 Stop 当成致命错误）
$prev = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $py -m twine --version 2>&1 | Out-Null
$twineOk = ($LASTEXITCODE -eq 0)
if (-not $twineOk) {
    Write-Host "未安装 twine，正在安装..." -ForegroundColor Yellow
    & $py -m pip install --user twine
    $twineOk = ($LASTEXITCODE -eq 0)
}
$ErrorActionPreference = $prev
if (-not $twineOk) {
    throw "twine 安装失败。请手动执行：`"$py`" -m pip install --user twine"
}

# 3. 取 token（优先剪贴板，避免粘贴只进一个字符）
if (-not $Token) { $Token = $env:PYPI_TOKEN }

if (-not $Token) {
    $clip = ""
    try { $clip = (Get-Clipboard -Raw -ErrorAction SilentlyContinue) } catch { $clip = "" }
    if ($clip) { $clip = $clip.Trim() }
    if ($clip -like "pypi-*") {
        Write-Host "已从剪贴板读取 token（长度 $($clip.Length)），直接使用。" -ForegroundColor Green
        $Token = $clip
    }
}

if (-not $Token) {
    Write-Host ""
    Write-Host "请粘贴 PyPI API Token（输入不显示，回车确认）：" -ForegroundColor Cyan
    $sec = Read-Host -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    try { $Token = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

$Token = $Token.Trim()
if (-not $Token) { throw "没有提供 token" }
if ($Token -notlike "pypi-*") {
    throw "token 格式不对：应以 pypi- 开头（当前长度 $($Token.Length)）"
}
if ($Token.Length -lt 40) {
    throw "token 太短（$($Token.Length) 字符），多半没复制完整。请重新复制后再运行。"
}

# 4. 上传
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = $Token
Write-Host "上传到 $repo ..." -ForegroundColor Cyan
$prev = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $py -m twine upload --repository $repo --non-interactive $wheel.FullName
$uploadCode = $LASTEXITCODE
$ErrorActionPreference = $prev
if ($uploadCode -ne 0) {
    throw "上传失败（常见原因：token 不完整、未开 2FA、版本号已存在）"
}

Write-Host ""
Write-Host "✅ 上传完成" -ForegroundColor Green
if ($TestPyPI) {
    Write-Host "验证：python -m pip install --index-url https://test.pypi.org/simple/ mcai-knowledge"
    Write-Host "演练通过后，去掉 -TestPyPI 再跑一次正式发布。"
} else {
    Write-Host "验证：python -m pip install --upgrade mcai-knowledge"
    Write-Host "页面：https://pypi.org/project/mcai-knowledge/"
    Write-Host ""
    Write-Host "下一步："
    Write-Host "  1. 把 server.json 的 YOURNAME 换成 GitHub 账号、version 改成 $($wheel.Name -replace '.*-([0-9.]+)-py3.*','$1')"
    Write-Host "  2. 提交 MCP 注册表 / 第三方目录"
}
