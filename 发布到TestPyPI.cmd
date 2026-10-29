@echo off
chcp 65001 >nul
echo Publishing to TestPyPI (rehearsal).
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\publish-pypi.ps1" -TestPyPI
echo.
pause