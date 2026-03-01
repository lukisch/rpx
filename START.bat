@echo off
title RPX - RolePlay Xtreme
cd /d "%~dp0"

REM Pruefe ob Python verfuegbar ist
python --version >NUL 2>&1
if errorlevel 1 (
    echo.
    echo  Python wurde nicht gefunden!
    echo  Bitte installiere Python 3.10+ von https://python.org
    echo.
    pause
    exit /b 1
)

REM Pruefe PySide6
python -c "import PySide6" 2>NUL
if errorlevel 1 (
    echo  PySide6 wird installiert...
    pip install PySide6 pygame
    echo.
)

REM Setze Encoding fuer Windows
set PYTHONIOENCODING=utf-8

REM Starte RPX
python "RPX_Pro_1.py"

if errorlevel 1 (
    echo.
    echo  RPX wurde mit einem Fehler beendet.
    echo  Details in: rpx_pro_data\rpx_pro.log
    echo.
    pause
)
