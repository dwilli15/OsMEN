@echo off
REM OsMEN Scheduled Tasks Uninstall Script for Windows
REM Run as Administrator to remove scheduled tasks

echo ============================================================
echo OsMEN Scheduled Tasks Uninstaller
echo ============================================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script requires Administrator privileges.
    echo Please right-click and "Run as administrator"
    pause
    exit /b 1
)

echo Removing scheduled tasks...
echo.

schtasks /delete /tn "OsMEN\WeeklyReview" /f 2>nul
if %errorlevel% equ 0 (
    echo [1/4] Removed: WeeklyReview
) else (
    echo [1/4] Not found: WeeklyReview
)

schtasks /delete /tn "OsMEN\DailyCleanup" /f 2>nul
if %errorlevel% equ 0 (
    echo [2/4] Removed: DailyCleanup
) else (
    echo [2/4] Not found: DailyCleanup
)

schtasks /delete /tn "OsMEN\HealthCheck" /f 2>nul
if %errorlevel% equ 0 (
    echo [3/4] Removed: HealthCheck
) else (
    echo [3/4] Not found: HealthCheck
)

schtasks /delete /tn "OsMEN\ObsidianSync" /f 2>nul
if %errorlevel% equ 0 (
    echo [4/4] Removed: ObsidianSync
) else (
    echo [4/4] Not found: ObsidianSync
)

echo.
echo ============================================================
echo Uninstallation complete!
echo ============================================================

pause
