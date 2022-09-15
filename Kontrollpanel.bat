echo off
:: Hämta git versionsnummer
WHERE git
IF %ERRORLEVEL% NEQ 0 (
   ECHO git command wasn't found
) ELSE (
   ECHO found git command
   IF EXIST ".git\" (
      ECHO found gitproject
      git describe --dirty --always --abbrev=1 > src\GIT_VERSION.txt
   ) ELSE (
      ECHO found no git folder
   )
)
set /p GIT_VERSION=<src\GIT_VERSION.txt

:: Get current dir
SET thispath=%~dp0
echo %thispath%

:: Set python runtime path
set PyRunTime=%thispath%\..\python3x64
::
set PATH=%PyRunTime%\python-current;%PyRunTime%\python-current\Scripts;%PyRunTime%\python-current\Lib\;%PATH%
set PYTHONPATH=%PyRunTime%\python-current;%PyRunTime%\python-current\lib;%PyRunTime%\python-current\libs;%PyRunTime%\python-current\DLLs;%PyRunTime%\python-current\

:: python --version
cd src
start pythonw kontrollpanel.py --ip=192.168.0.130

if errorlevel 1 (
   echo Failure Reason Given is %errorlevel%
   pause
   exit /b %errorlevel%
)
