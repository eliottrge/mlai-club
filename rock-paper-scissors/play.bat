@echo off
rem Double-click to play. Installs any missing libraries into a compatible Python (needs internet the first time).
rem TensorFlow only works with Python 3.10, 3.11 or 3.12, so newer/older Pythons are skipped.
rem The Microsoft Store Python is skipped too: its very long install path breaks the TensorFlow install.
cd /d "%~dp0"

set PY=
call :find
if not defined PY (
    echo No compatible Python ^(3.10 - 3.12^) found. Trying to install Python 3.11 automatically...
    winget install -e --id Python.Python.3.11 --scope user --accept-package-agreements --accept-source-agreements
    call :find
)
if not defined PY (
    echo.
    echo Could not find or install a compatible Python. Please install Python 3.11 from
    echo https://www.python.org/downloads/release/python-3119/  ^(tick "Add python.exe to PATH"^),
    echo then double-click play.bat again.
    pause
    exit /b 1
)
echo Using %PY%

rem ---- install the libraries only if something is missing ----
%PY% -c "import tensorflow, tf_keras, cv2, numpy" >nul 2>&1
if errorlevel 1 (
    echo Installing libraries. This can take a few minutes...
    %PY% -m pip install --no-warn-script-location -r requirements.txt
    if errorlevel 1 goto fail
    echo Setup complete.
)

%PY% rps_game.py %*
if errorlevel 1 pause
exit /b 0

:fail
echo.
echo Setup failed. Check your internet connection and try again.
echo If the error mentions a "long path" or "No such file or directory", you are probably using the
echo Microsoft Store version of Python. Install Python 3.11 from python.org instead
echo ^(https://www.python.org/downloads/release/python-3119/^), then run play.bat again.
pause
exit /b 1

:find
rem Sets PY to the first compatible Python found.
for %%C in ("py -3.11" "py -3.12" "py -3.10" "python3.11" "python3.12" "python3.10" "python" "python3" "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%LOCALAPPDATA%\Programs\Python\Python310\python.exe") do (
    if not defined PY (
        %%~C -c "import sys; p=sys.executable+sys.prefix; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,12) and 'WindowsApps' not in p else 1)" >nul 2>&1 && set "PY=%%~C"
    )
)
if defined PY echo %PY%| "%SystemRoot%\System32\find.exe" ":" >nul && set PY="%PY%"
goto :eof
