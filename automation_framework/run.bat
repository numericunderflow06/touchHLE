@echo off
REM TouchHLE Automated Research Pipeline Runner (Windows)
REM
REM Usage: run.bat [--reset]
REM   --reset: Clear persistent memory and start fresh

cd /d "%~dp0"

if "%1"=="--reset" (
    echo Resetting persistent memory...
    del /q PERSISTENT_MEMORY.md 2>nul
    rmdir /s /q sessions 2>nul
    mkdir sessions
    echo Reset complete.
)

echo ========================================
echo   TouchHLE Automation Pipeline
echo ========================================
echo.
echo Configuration:
echo   - Model: Claude Opus 4.5
echo   - Claude Code: v2.1.2
echo   - Working Dir: D:/touchHLE_src
echo   - Max Retries: 20
echo.
echo Press Ctrl+C to stop at any time.
echo.

REM Run the Python automation runner
python automation_runner.py

set exit_code=%errorlevel%
echo.
echo Pipeline exited with code: %exit_code%
exit /b %exit_code%
