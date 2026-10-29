@echo off
chcp 65001 >nul
echo Install mcp-publisher
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\install-mcp-publisher.ps1"
echo.
pause