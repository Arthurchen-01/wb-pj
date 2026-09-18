@echo off
chcp 65001 >nul
rem ============================================================
rem  run-unlock-DEBUG.bat - diagnostics: capture full output
rem  Logs produced in this folder:
rem    ps-run-stdout.log  (normal output)
rem    ps-run-stderr.log  (errors - most important)
rem ============================================================
cd /d "%~dp0"
echo ============================================================
echo  Running unlock-workbuddy.ps1 (debug mode)
echo  Output will be saved to log files in this folder.
echo ============================================================
if exist "%~dp0ps-run-stdout.log" del "%~dp0ps-run-stdout.log"
if exist "%~dp0ps-run-stderr.log" del "%~dp0ps-run-stderr.log"
echo [ENV] PS version: > "%~dp0ps-run-stdout.log"
powershell -NoProfile -Command "$PSVersionTable.PSVersion.ToString()" >> "%~dp0ps-run-stdout.log" 2>&1
echo [RUN] Starting unlock-workbuddy.ps1 ... >> "%~dp0ps-run-stdout.log"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0unlock-workbuddy.ps1" %* >> "%~dp0ps-run-stdout.log" 2>> "%~dp0ps-run-stderr.log"
echo [RUN] ExitCode: %errorlevel% >> "%~dp0ps-run-stdout.log"
echo.
echo ============================================================
echo  Done. ExitCode: %errorlevel%
echo  Stdout log:  ps-run-stdout.log
echo  Stderr log:  ps-run-stderr.log
echo ============================================================
pause
