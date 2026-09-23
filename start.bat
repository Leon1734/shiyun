@echo off
cd /d "%~dp0"

echo.
echo   Chinese Poetry Desktop v7.0
echo   344420 poems + 278 prose / 13452 poets
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Try the standalone version: dist\诗韵\诗韵.exe
    pause
    exit /b 1
)

if not exist data\poetry.db (
    echo ERROR: Database not found - run json_to_sqlite.py first
    pause
    exit /b 1
)

echo Starting...
python poetry_desktop.py

echo.
echo Exited with code: %errorlevel%
pause
