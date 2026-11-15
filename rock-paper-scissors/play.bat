@echo off
rem Double-click to play. The first run installs everything automatically (needs internet).
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto run

rem ---- find Python ----
set PY=
py -3.11 --version >nul 2>&1 && set PY=py -3.11
if not defined PY py -3.12 --version >nul 2>&1 && set PY=py -3.12
if not defined PY py -3.10 --version >nul 2>&1 && set PY=py -3.10
if not defined PY python --version >nul 2>&1 && set PY=python
if not defined PY (
    echo Python was not found. Install Python 3.11 from https://www.python.org/downloads/
    echo ^(tick "Add python.exe to PATH" in the installer^), then double-click play.bat again.
    pause
    exit /b 1
)

echo First-time setup: installing libraries. This can take a few minutes...
%PY% -m venv .venv || goto fail
".venv\Scripts\python.exe" -m pip install --upgrade pip || goto fail
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto fail
echo Setup complete.

:run
".venv\Scripts\python.exe" rps_game.py %*
if errorlevel 1 pause
exit /b 0

:fail
echo.
echo Setup failed. Delete the ".venv" folder, check your internet connection, and try again.
rmdir /s /q .venv 2>nul
pause
exit /b 1
