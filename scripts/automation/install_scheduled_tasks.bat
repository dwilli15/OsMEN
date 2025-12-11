@echo off
REM OsMEN Scheduled Tasks Installation Script for Windows
REM Run as Administrator to install scheduled tasks

setlocal enabledelayedexpansion

echo ============================================================
echo OsMEN Scheduled Tasks Installer
echo ============================================================
echo.

REM Get script directory and set base path
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\.."
set "BASE_PATH=%CD%"

echo Base path: %BASE_PATH%
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script requires Administrator privileges.
    echo Please right-click and "Run as administrator"
    pause
    exit /b 1
)

REM Create task folder
schtasks /query /tn "OsMEN" >nul 2>&1
if %errorlevel% neq 0 (
    echo Creating OsMEN task folder...
)

echo.
echo Installing scheduled tasks...
echo.

REM 1. Weekly Review - Sundays at 2 AM
echo [1/4] Installing Weekly Review task...
schtasks /create /tn "OsMEN\WeeklyReview" ^
    /tr "cmd /c cd /d \"%BASE_PATH%\" && python scripts\automation\weekly_review.py" ^
    /sc weekly /d SUN /st 02:00 ^
    /ru SYSTEM /rl HIGHEST ^
    /f
if %errorlevel% equ 0 (
    echo       SUCCESS: Weekly Review scheduled for Sundays at 2:00 AM
) else (
    echo       FAILED: Could not create Weekly Review task
)

REM 2. Daily Cleanup - Daily at 3 AM
echo [2/4] Installing Daily Cleanup task...
schtasks /create /tn "OsMEN\DailyCleanup" ^
    /tr "cmd /c cd /d \"%BASE_PATH%\" && python scripts\automation\lifecycle_automation.py --action daily" ^
    /sc daily /st 03:00 ^
    /ru SYSTEM /rl HIGHEST ^
    /f
if %errorlevel% equ 0 (
    echo       SUCCESS: Daily Cleanup scheduled for 3:00 AM
) else (
    echo       FAILED: Could not create Daily Cleanup task
)

REM 3. Health Check - Every 5 minutes
echo [3/4] Installing Health Check task...
schtasks /create /tn "OsMEN\HealthCheck" ^
    /tr "cmd /c cd /d \"%BASE_PATH%\" && python infrastructure\health_monitor.py --check" ^
    /sc minute /mo 5 ^
    /ru SYSTEM ^
    /f
if %errorlevel% equ 0 (
    echo       SUCCESS: Health Check scheduled every 5 minutes
) else (
    echo       FAILED: Could not create Health Check task
)

REM 4. Obsidian Sync - Every 30 minutes
echo [4/4] Installing Obsidian Sync task...
schtasks /create /tn "OsMEN\ObsidianSync" ^
    /tr "cmd /c cd /d \"%BASE_PATH%\" && python tools\obsidian\obsidian_sync_watcher.py --sync" ^
    /sc minute /mo 30 ^
    /ru SYSTEM ^
    /f
if %errorlevel% equ 0 (
    echo       SUCCESS: Obsidian Sync scheduled every 30 minutes
) else (
    echo       FAILED: Could not create Obsidian Sync task
)

echo.
echo ============================================================
echo Installation complete!
echo.
echo View tasks in Task Scheduler under "OsMEN" folder
echo Or run: schtasks /query /tn "OsMEN\*"
echo ============================================================

pause
