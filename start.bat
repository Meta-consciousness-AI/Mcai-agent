@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY=python"
where python >nul 2>nul
if errorlevel 1 set "PY=%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"

if not exist "%PY%" (
  echo 未找到 Python，请先安装 Python 3.10+（含 python-docx、lxml）。
  pause
  exit /b 1
)

echo 构建知识库…
"%PY%" -m mcai build --home "%~dp0"
if errorlevel 1 pause & exit /b 1

echo.
echo 启动服务（含自动驾驶：每 5 分钟检查语料与健康状态）
echo 浏览器访问 http://127.0.0.1:8787
"%PY%" -m mcai serve --home "%~dp0" --port 8787 --autopilot 300
