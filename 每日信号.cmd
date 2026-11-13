@echo off
chcp 65001 >nul

set "ROOT=C:\Users\HP\Documents\deepseek-harness\default-workspace\mca-agent"
cd /d "%ROOT%"

set "PYTHONIOENCODING=utf-8"
set "PY=C:\Users\HP\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" tools\daily_signal.py
echo.
pause
