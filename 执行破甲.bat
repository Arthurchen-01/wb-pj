@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo  WorkBuddy Unlock v2.0  --  ONE CLICK: all products
echo  = auto-discover WorkBuddy* / patch / verify =
echo ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0unlock-workbuddy.ps1" -All -Verify
echo.
echo ============================================================
echo Done. Details in unlock-log.txt
echo !! Fully quit the apps (incl. tray icons) and reopen them.
echo ============================================================
pause
