@echo off
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set "PYTHON_CMD=python"
python --version >nul 2>&1
if errorlevel 1 (
    py -3 --version >nul 2>&1
    if errorlevel 1 (
        echo [FEHLER] Python nicht gefunden!
        pause
        exit /b 1
    )
    set "PYTHON_CMD=py -3"
)
echo Baue RPX_Pro...
powershell -NoProfile -Command "Get-ChildItem -LiteralPath 'build','dist' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force"
%PYTHON_CMD% -m PyInstaller --noconfirm --clean RPX_Pro.spec
if errorlevel 1 pause
