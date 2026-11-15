@echo off
rem Double-click to play. Installs any missing libraries into your Python (needs internet the first time).
cd /d "%~dp0"

rem ---- find Python: the normal "python" first, then the py launcher ----
set PY=
python --version >nul 2>&1 && set PY=python
if not defined PY py -3.11 --version >nul 2>&1 && set PY=py -3.11
if not defined PY py -3.12 --version >nul 2>&1 && set PY=py -3.12
if not defined PY py -3.10 --version >nul 2>&1 && set PY=py -3.10
if not defined PY (
    echo Python was not found. Trying to install Python 3.11 automatically...
    winget install -e --id Python.Python.3.11 --scope user --accept-package-agreements --accept-source-agreements
    py -3.11 --version >nul 2>&1 && set PY=py -3.11
)
if not defined PY (
    echo.
    echo Could not install Python automatically. Please install Python 3.11 from
    echo https://www.python.org/downloads/  ^(tick "Add python.exe to PATH"^),
    echo then double-click play.bat again.
    pause
    exit /b 1
)

rem ---- install the libraries only if something is missing ----
%PY% -c "import tensorflow, tf_keras, cv2, numpy" >nul 2>&1
if errorlevel 1 (
    echo Installing libraries into this Python. This can take a few minutes...
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 goto fail
    echo Setup complete.
)

%PY% rps_game.py %*
if errorlevel 1 pause
exit /b 0

:fail
echo.
echo Setup failed. Check your internet connection. TensorFlow needs Python 3.10, 3.11 or 3.12;
echo if you have a newer Python, install Python 3.11 and try again.
pause
exit /b 1
