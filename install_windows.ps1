# install_windows.ps1
# Native Installation Script for Windows 10/11
# Assumes ROS 2 Jazzy is installed and "call C:\dev\ros2_jazzy\local_setup.bat" works or is in PATH.

Write-Host "🚀 Starting Native Installation for Gazebo Swarm Sim (Windows)..." -ForegroundColor Green

# 1. Check Python
$pythonVersion = python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found! Please install Python 3.10+ and add to PATH." -ForegroundColor Red
    exit 1
}
Write-Host "   Using Python: $pythonVersion"

# 2. Python Environment
Write-Host "🐍 Setting up Python Virtual Environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
}
.\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "   Installing pip requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. Check for Missing Repositories
Write-Host "📥 Checking source repositories..." -ForegroundColor Yellow

# Multi-Robot-Graph-SLAM
if (-not (Test-Path "src\Multi-Robot-Graph-SLAM\mrg_slam.repos")) {
    Write-Host "   Cloning Multi-Robot-Graph-SLAM..."
    if (Test-Path "src\Multi-Robot-Graph-SLAM") { Remove-Item -Recurse -Force "src\Multi-Robot-Graph-SLAM" }
    git clone https://github.com/aserbremen/Multi-Robot-Graph-SLAM src/Multi-Robot-Graph-SLAM
}

# PX4-gazebo-models
if (-not (Test-Path "src\swarm_sim_pkg\swarm_sim\assets\PX4-gazebo-models\.git")) {
    Write-Host "   Cloning PX4-gazebo-models..."
    if (Test-Path "src\swarm_sim_pkg\swarm_sim\assets\PX4-gazebo-models") { Remove-Item -Recurse -Force "src\swarm_sim_pkg\swarm_sim\assets\PX4-gazebo-models" }
    git clone https://github.com/PX4/PX4-gazebo-models src/swarm_sim_pkg/swarm_sim\assets\PX4-gazebo-models
}

# 4. VCS Import
Write-Host "🔄 Importing dependencies via vcstool..." -ForegroundColor Yellow
$vcsPath = "$PSScriptRoot\venv\Scripts\vcs.exe"
if (-not (Test-Path $vcsPath)) {
    Write-Host "⚠️ vcs.exe not found in venv! Trying global..." -ForegroundColor Yellow
    $vcsPath = "vcs"
}

if (Test-Path "src\Multi-Robot-Graph-SLAM\mrg_slam.repos") {
    & $vcsPath import src --input src\Multi-Robot-Graph-SLAM\mrg_slam.repos
} else {
    Write-Host "⚠️ mrg_slam.repos not found, skipping vcs import." -ForegroundColor Yellow
}

# 5. Build Workspace
Write-Host "🔨 Building ROS 2 Workspace..." -ForegroundColor Yellow

# Clean previous build artifacts (Fixes layout mismatch errors)
Write-Host "🧹 Cleaning previous build artifacts..." -ForegroundColor Yellow
if (Test-Path "install") { Remove-Item -Recurse -Force "install" -ErrorAction SilentlyContinue }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" -ErrorAction SilentlyContinue }
if (Test-Path "log") { Remove-Item -Recurse -Force "log" -ErrorAction SilentlyContinue }

# Try to source ROS 2 if standard location (adjust if needed)
# Try to source ROS 2 (Check common locations)
$ros2Paths = @(
    "C:\dev\ros2_jazzy\local_setup.ps1",
    "C:\opt\ros\jazzy\x64\local_setup.ps1",
    "C:\ROS2\jazzy\local_setup.ps1",
    "C:\Program Files\ros2_jazzy\local_setup.ps1"
)

$rosLoaded = $false
foreach ($path in $ros2Paths) {
    if (Test-Path $path) {
        Write-Host "   Sourcing ROS 2 from: $path"
        . $path
        $rosLoaded = $true
        break
    }
}

if (-not $rosLoaded) {
    Write-Host "⚠️ Could not find ROS 2 installation automatically." -ForegroundColor Red
    Write-Host "   Please ensure ROS 2 Jazzy is installed and local_setup.ps1 is reachable."
    Write-Host "   You can manually source it before running this script."
}


$colconPath = "$PSScriptRoot\venv\Scripts\colcon.exe"
if (-not (Test-Path $colconPath)) {
    Write-Host "⚠️ colcon.exe not found in venv! Trying global..." -ForegroundColor Yellow
    $colconPath = "colcon"
}

& $colconPath build --merge-install --parallel-workers 1

Write-Host "✅ Installation Complete!" -ForegroundColor Green
Write-Host "   Run '.\run_windows.ps1' to start the simulation."
