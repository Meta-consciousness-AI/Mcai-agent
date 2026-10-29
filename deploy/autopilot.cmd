@echo off
rem 由计划任务调用：一轮自动驾驶（检查语料、必要时重建、健康自检）
setlocal
set "PY=python"
where python >nul 2>nul
if errorlevel 1 set "PY=%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
set "HOME_DIR=%~dp0.."
"%PY%" -m mcai autopilot --once --home "%HOME_DIR%" --port 8787 >> "%HOME_DIR%\data\autopilot.log" 2>&1
endlocal
