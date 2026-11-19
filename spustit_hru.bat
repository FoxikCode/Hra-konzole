@echo off
chcp 65001 >nul
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 mechova_hra.py
) else (
    python mechova_hra.py
)

if not %errorlevel% equ 0 (
    echo.
    echo Hru se nepodarilo spustit. Zkontroluj, ze je nainstalovany Python 3.
)
pause
