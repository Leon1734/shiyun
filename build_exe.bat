@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo   ====================================
echo     GuShiCi Desktop v7.0 - Build EXE
echo   ====================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller -q
)

echo Building...
pyinstaller build.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo BUILD FAILED
    pause
    exit /b 1
)

echo.
echo Setting up data directory...

if not exist "dist\诗韵\data" (
    powershell -Command "New-Item -ItemType Junction -Path 'dist\诗韵\data' -Target '%~dp0data' | Out-Null"
    if errorlevel 1 (
        echo Junction failed, copying data instead (may take a while)...
        xcopy /E /I /Y "data" "dist\诗韵\data"
    )
)

echo.
echo   ====================================
echo     BUILD COMPLETE
echo   ====================================
echo.
echo   Output: dist\诗韵\诗韵.exe
echo   Data:   dist\诗韵\data\ (linked to project data)
echo.
echo   To distribute: copy the whole dist\诗韵 folder
echo   (or replace the data junction with a real copy)
echo.
pause
