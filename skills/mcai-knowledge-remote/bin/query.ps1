param(
    [Parameter(Position=0)][string]$Command = "answer",
    [Parameter(Position=1)][string]$Arg = "",
    [string]$BaseUrl = $env:MCAI_BASE_URL
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$OutputEncoding = [System.Text.Encoding]::UTF8
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONIOENCODING = "utf-8"
if (-not $BaseUrl) {
    $BaseUrl = "https://mcai-mcp-public-338698-11-1316838521.sh.run.tcloudbase.com/api/v1"
}
$BaseUrl = $BaseUrl.TrimEnd("/")

$py = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python -ErrorAction SilentlyContinue }
if ($py) {
    $cliArgs = @($Command)
    if ($Arg) { $cliArgs += $Arg }
    & $py.Source (Join-Path $dir "mcai_client.py") @cliArgs
    exit $LASTEXITCODE
}

# Fallback: curl.exe (Windows 10+), answer only.
if ($Command -ne "answer" -or -not $Arg) {
    @{ ok = $false; error = "no_python"; detail = "需要 python3/python，或只用 answer 命令" } |
        ConvertTo-Json -Compress
    exit 0
}
$curl = Get-Command curl.exe -ErrorAction SilentlyContinue
if (-not $curl) {
    @{ ok = $false; error = "no_curl"; detail = "需要 python3/python 或 curl.exe" } |
        ConvertTo-Json -Compress
    exit 0
}
$tmp = [System.IO.Path]::GetTempFileName()
try {
    $json = @{ question = $Arg } | ConvertTo-Json -Compress
    [System.IO.File]::WriteAllText($tmp, $json, (New-Object System.Text.UTF8Encoding($false)))
    & $curl.Source -sS -m 90 -X POST "$BaseUrl/answer" `
        -H "Content-Type: application/json; charset=utf-8" `
        -H "User-Agent: mcai-remote-skill/1.0" `
        --data-binary "@$tmp"
}
catch {
    @{ ok = $false; error = $_.Exception.Message; detail = "远程知识库暂时不可用" } |
        ConvertTo-Json -Compress
}
finally {
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}
