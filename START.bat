@echo off
title RPX - RolePlay Xtreme
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM Pruefe ob Python verfuegbar ist
set "PYTHON_CMD=python"
python --version >NUL 2>&1
if errorlevel 1 (
    py -3 --version >NUL 2>&1
    if errorlevel 1 (
        echo.
        echo  Python wurde nicht gefunden!
        echo  Bitte installiere Python 3.10+ von https://python.org
        echo.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=py -3"
)

REM Pruefe PySide6
%PYTHON_CMD% -c "import PySide6" 2>NUL
if errorlevel 1 (
    echo  PySide6 wird installiert...
    %PYTHON_CMD% -m pip install PySide6 pygame
    echo.
)

REM Starte RPX
%PYTHON_CMD% "RPX_Pro_1.py"

if errorlevel 1 (
    echo.
    echo  RPX wurde mit einem Fehler beendet.
    echo  Details in: rpx_pro_data\rpx_pro.log
    echo.
    pause
)
