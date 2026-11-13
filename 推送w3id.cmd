@echo off
chcp 65001 >nul
cd /d "%~dp0.build\w3id-fork"
echo Pushing add-mcai to GitHub...
echo.
git push origin add-mcai
if errorlevel 1 (
    echo.
    echo Push failed. Check GitHub login or network.
) else (
    echo.
    echo Done. Next: open the compare page and create a pull request.
)
pause
