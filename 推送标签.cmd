@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem Usage:  this .cmd <tag-name>
rem Without an argument, push the most recent tag (git describe --tags --abbrev=0).
rem The real work (IP pinning, hosts backup/restore, verification) is in
rem deploy\push-github.ps1 -Tag, so this file never calls git push directly.

set "TAG=%~1"
if not "%TAG%"=="" goto have_tag

rem Note: --abbrev=0 must be quoted inside for /f, otherwise cmd splits it at "="
rem and git reports "Not a valid object name 0".
for /f "delims=" %%t in ('git describe --tags "--abbrev=0" 2^>nul') do set "TAG=%%t"
if "%TAG%"=="" (
    echo.
    echo No tag found in this repository.
    echo Create one first, for example:  git tag -a ^<tag^> -m "release message"
    echo.
    pause
    exit /b 1
)

:have_tag
echo Pushing tag %TAG% to GitHub...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\push-github.ps1" -Tag "%TAG%"
if errorlevel 1 (
    echo.
    echo Push failed. If it asks for administrator rights, rerun this from an
    echo elevated PowerShell window; otherwise check the tag name and network.
) else (
    echo.
    echo Tag pushed. Next: create a GitHub Release from this tag in the web UI.
)
pause
