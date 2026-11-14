@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Pushing tag v0.3.8 to GitHub...
echo.
git push origin v0.3.8
if errorlevel 1 (
    echo.
    echo Push failed. Check GitHub login or network.
) else (
    echo.
    echo Tag pushed. Next: create a GitHub Release from tag v0.3.8.
)
pause