@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo  WorkBuddy Unlock v2.0  --  TARGET: WorkBuddyAI only
echo ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0unlock-workbuddy.ps1" -AI -Verify
echo.
echo Done. Fully quit WorkBuddyAI (incl. tray icon) and reopen.
pause
