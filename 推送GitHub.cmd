@echo off
chcp 65001 >nul
echo Push to GitHub
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\push-github.ps1"
echo.
pause