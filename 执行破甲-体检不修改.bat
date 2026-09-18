@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo  WorkBuddy Unlock v2.0  --  CHECK ONLY (no file changed)
echo  靶点状态: loose=已破 / strict=未破 / stale=旧版 / notag=无政策块
echo ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0unlock-workbuddy.ps1" -Auto -Diagnose
echo.
echo Done. 完整结果见 unlock-log.txt
pause
