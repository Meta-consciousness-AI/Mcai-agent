@echo off
chcp 65001 >nul
echo Publishing to PyPI (production).
echo If this is your first time, run the TestPyPI script first.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\publish-pypi.ps1"
echo.
pause