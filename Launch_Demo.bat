@echo off
setlocal
cd /d "%~dp0"
title EvolutionaryChemistry demo
echo ==== EvolutionaryChemistry demo launcher ====
set "VPY=.venv\Scripts\python.exe"
if exist "%VPY%" goto have_venv

rem ---- find a Python 3.10+ (python.org install recommended; tick "tcl/tk" and "Add to PATH") ----
set "PY="
python -c "import sys; assert sys.version_info>=(3,10)" >nul 2>&1 && set "PY=python"
if not defined PY ( py -3 -c "import sys; assert sys.version_info>=(3,10)" >nul 2>&1 && set "PY=py -3" )
if not defined PY (
  echo ERROR: Python 3.10 or newer was not found.
  echo Install it from https://www.python.org/downloads/ ^(tick "Add python.exe to PATH" and "tcl/tk"^), then run this file again.
  pause & exit /b 1
)
%PY% -c "import tkinter" >nul 2>&1
if errorlevel 1 (
  echo ERROR: your Python has no Tkinter. Re-run the Python installer, choose Modify and tick "tcl/tk and IDLE".
  pause & exit /b 1
)
echo Creating local virtual environment in .venv using: %PY%
%PY% -m venv .venv
if errorlevel 1 ( echo ERROR: could not create .venv & pause & exit /b 1 )

:have_venv
if exist ".venv\installed.ok" goto run
echo Installing requirements ^(first run only, needs internet, about 150 MB^) ...
"%VPY%" -m pip install --upgrade pip >nul
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: pip install failed. Check your internet connection or proxy, then run again.
  pause & exit /b 1
)
echo ok> ".venv\installed.ok"

:run
echo Launching GUI ...
"%VPY%" gui.py %*
if errorlevel 1 ( echo ERROR: the GUI exited with an error ^(see messages above^). & pause & exit /b 1 )
endlocal
