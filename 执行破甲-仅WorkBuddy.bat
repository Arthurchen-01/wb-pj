@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo  WorkBuddy Unlock v2.0  --  TARGET: WorkBuddy only
echo ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0unlock-workbuddy.ps1" -Verify
echo.
echo Done. Fully quit WorkBuddy (incl. tray icon) and reopen.
pause
