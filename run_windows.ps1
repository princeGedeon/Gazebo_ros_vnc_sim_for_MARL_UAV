# run_windows.ps1
# Launch script for Windows

# Force GPU Usage (if NVIDIA)
$Env:NVIDIA_VISIBLE_DEVICES = "all"
$Env:NVIDIA_DRIVER_CAPABILITIES = "all"
$Env:QT_OPENGL = "desktop" # Force OpenGL desktop mode for PyQt/Rqt

# Source ROS 2 (Check common locations)
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
    Write-Host "   Script might fail if 'ros2' is not in PATH."
}

# Source venv
if (Test-Path "venv\Scripts\Activate.ps1") {
    . "venv\Scripts\Activate.ps1"
}

# Source local workspace
if (Test-Path "install\setup.ps1") {
    . "install\setup.ps1"
}

Write-Host "🚁 Starting Simulation (Windows Native)..." -ForegroundColor Cyan

Write-Host "🚁 Starting Simulation (Windows Native)..." -ForegroundColor Cyan

# 1. Launch Gazebo + ROS 2
Write-Host "[1/3] Launching Gazebo Simulation..."
$gazeboProcess = Start-Process -FilePath "ros2" -ArgumentList "launch", "swarm_sim", "super_simulation.launch.py", "num_drones:=3", "slam:=true" -PassThru -NoNewWindow
Start-Sleep -Seconds 20

# 2. Launch RViz
Write-Host "[2/3] Launching RViz..."
$rvizConfig = "$PSScriptRoot\rviz_configs\dynamic_swarm.rviz"
# Regenerate config if python script works on windows
python scripts/generate_rviz.py 3 $rvizConfig
Start-Process -FilePath "rviz2" -ArgumentList "-d", $rvizConfig -PassThru -NoNewWindow

# 3. Launch Training
Write-Host "[3/3] Launching Training (Case 1)..."
python src/swarm_sim_pkg/swarm_sim/training/train_mappo.py --num-drones 3 --max-steps 1000 --output-dir outputs/case_1

# Cleanup on exit
Stop-Process -Id $gazeboProcess.Id -Force -ErrorAction SilentlyContinue
