@echo off
REM ============================================================
REM  Abhijeet Work Hub - one click launcher
REM  Double click this file to start the software.
REM
REM  No machine-specific path is hard-coded here.
REM  Settings live in .env  (copy .env.example to .env).
REM ============================================================
title Work Hub
cd /d "%~dp0"

echo.
echo   ==========================================
echo     WORK HUB
echo   ==========================================
echo.

REM --- find a Python that already has Flask --------------------
set "PY="
for %%C in (python py python3) do (
    if not defined PY (
        %%C -c "import flask" >nul 2>&1 && set "PY=%%C"
    )
)

REM --- fallback: standard per-user Python install location ------
if not defined PY (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
        if not defined PY (
            if exist "%%~fD\python.exe" (
                "%%~fD\python.exe" -c "import flask" >nul 2>&1 && set "PY=%%~fD\python.exe"
            )
        )
    )
)

if not defined PY (
    echo   [X] Python with Flask was not found.
    echo.
    echo       1. Install Python from https://www.python.org/downloads/
    echo          and tick "Add python.exe to PATH" during setup.
    echo       2. Open a new terminal and run:
    echo.
    echo            pip install flask
    echo.
    pause
    exit /b 1
)

echo   [OK] Python: %PY%
echo.

echo   Building the project catalogue...
%PY% build_catalog.py
echo.

echo   ------------------------------------------
echo     Open this URL in your browser:
echo       http://127.0.0.1:5000
echo   ------------------------------------------
echo.
echo   Press Ctrl+C in this window to stop.
echo.

start "" http://127.0.0.1:5000
%PY% app.py

echo.
echo   Work Hub stopped.
pause