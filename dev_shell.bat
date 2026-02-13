@echo off
echo ========================================================
echo 🛠️  Setting up Development Environment...
echo ========================================================

REM 1. Visual Studio 2022
if defined VSCMD_VER (
    echo ✅ Visual Studio Environment already active.
) else (
    set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022"
    set "VC_VARS=VC\Auxiliary\Build\vcvars64.bat"
    
    if exist "%VS_PATH%\Community\%VC_VARS%" (
        call "%VS_PATH%\Community\%VC_VARS%"
    ) else if exist "%VS_PATH%\Enterprise\%VC_VARS%" (
        call "%VS_PATH%\Enterprise\%VC_VARS%"
    ) else if exist "%VS_PATH%\Professional\%VC_VARS%" (
        call "%VS_PATH%\Professional\%VC_VARS%"
    ) else (
        echo ⚠️ WARNING: Visual Studio 2022 not found automatically.
        echo    Compilations might fail.
    )
)

REM 2. ROS 2 Jazzy
set "ROS2_SOURCED="
if exist "C:\dev\ros2_jazzy\local_setup.bat" (
    call "C:\dev\ros2_jazzy\local_setup.bat"
    set ROS2_SOURCED=1
) else if exist "C:\opt\ros\jazzy\x64\local_setup.bat" (
    call "C:\opt\ros\jazzy\x64\local_setup.bat"
    set ROS2_SOURCED=1
) else if exist "C:\Program Files\ros2_jazzy\local_setup.bat" (
    call "C:\Program Files\ros2_jazzy\local_setup.bat"
    set ROS2_SOURCED=1
) else (
    echo ❌ ERROR: ROS 2 not found automatically.
    echo    Please set environment variables manually or edit this script.
)

if defined ROS2_SOURCED (
    echo ✅ ROS 2 Jazzy Sourced.
)

REM 3. Python Virtual Environment
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
    echo ✅ Python Virtual Environment Activated.
) else (
    echo ❌ ERROR: 'venv' not found. Run setup_and_run.bat first!
)

echo.
echo ========================================================
echo 🚀 Environment Ready!
echo You can now run: colcon, ros2, python, etc.
echo ========================================================
cmd /k
