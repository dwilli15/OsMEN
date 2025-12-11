@echo off
echo Killing VS Code processes...
taskkill /IM Code.exe /F
taskkill /IM "Code - Insiders.exe" /F

echo.
echo Cleaning Copilot Cache...
set "CACHE_DIR=%APPDATA%\Code\User\globalStorage"
if exist "%CACHE_DIR%\github.copilot*" (
    echo Found cache files. Deleting...
    for /d %%G in ("%CACHE_DIR%\github.copilot*") do rd /s /q "%%G"
    del /q "%CACHE_DIR%\github.copilot*"
    echo Cleanup complete.
) else (
    echo No Copilot cache files found.
)

echo.
echo Done. You can restart VS Code now.
pause
