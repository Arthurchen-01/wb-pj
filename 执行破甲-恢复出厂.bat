@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo  WorkBuddy Unlock v2.0  --  RESTORE all .unlockbak
echo  This reverts every patched file back to factory state.
echo ============================================================
set /p go=Type Y and press Enter to continue:
if /i not "%go%"=="Y" goto :cancel
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0unlock-workbuddy.ps1" -Auto -Restore
echo.
echo Done. 已恢复出厂。
pause
exit /b
:cancel
echo Cancelled.
pause
