@echo off
chcp 65001 >nul
set PY=C:\Users\HP\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe
set TARGET=%TEMP%\mcai-verify-030

echo Installing mcai-knowledge into %TARGET% ...
"%PY%" -m pip install --no-cache-dir --quiet --upgrade --target "%TARGET%" mcai-knowledge
if errorlevel 1 (
  echo Install failed. Check network or proxy.
  pause
  exit /b 1
)

echo.
echo Installed version:
set PYTHONPATH=%TARGET%
"%PY%" -m mcai --version
echo.
echo Done. Target folder: %TARGET%
pause