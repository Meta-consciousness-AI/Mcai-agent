@echo off
chcp 65001 >nul
echo Push to Gitee (token from clipboard)
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\push-gitee.ps1"
echo.
pause