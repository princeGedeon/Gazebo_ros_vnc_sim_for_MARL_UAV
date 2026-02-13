@echo off
setlocal
echo ========================================================
echo 🚀 Auto-detecting Visual Studio 2022 Environment...
echo ========================================================

REM Check if already in VS Prompt
if defined VSCMD_VER (
    echo ✅ Visual Studio Environment already active.
    goto :RunScripts
)

REM Try to find and call vcvars64.bat
set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022"
set "VC_VARS=VC\Auxiliary\Build\vcvars64.bat"

if exist "%VS_PATH%\Community\%VC_VARS%" (
    echo 🔧 Found VS 2022 Community. Initializing...
    call "%VS_PATH%\Community\%VC_VARS%"
) else if exist "%VS_PATH%\Enterprise\%VC_VARS%" (
    echo 🔧 Found VS 2022 Enterprise. Initializing...
    call "%VS_PATH%\Enterprise\%VC_VARS%"
) else if exist "%VS_PATH%\Professional\%VC_VARS%" (
    echo 🔧 Found VS 2022 Professional. Initializing...
    call "%VS_PATH%\Professional\%VC_VARS%"
) else (
    echo ⚠️ Could not find Visual Studio 2022 in standard paths.
    echo    Build might fail if not running in Native Tools Command Prompt.
)

:RunScripts
echo.
echo ========================================================
echo 📦 1. Running Installation Script...
echo ========================================================
powershell -ExecutionPolicy Bypass -File ".\install_windows.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Installation Failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo 🚁 2. Launching Simulation...
echo ========================================================
powershell -ExecutionPolicy Bypass -File ".\run_windows.ps1"

pause
