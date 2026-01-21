#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "==========================================="
echo "   SWARM SIMULATION AUTO-LAUNCHER"
echo "==========================================="
echo "Realised by Prince Gedeon"
echo ""

# 1. Fix Git Safety (Redundant but safe)
git config --global --add safe.directory '*'

# 2. Clean Problematic Build Artifacts (Fixes 'Is a directory' error)
echo "[1/4] Cleaning build artifacts..."
rm -rf build/cslam_common_interfaces install/cslam_common_interfaces
rm -rf build/swarm_sim install/swarm_sim share/swarm_sim
# rm -rf build/ install/ # Uncomment for full clean buffer

# 3. Build Workspace
echo "[2/4] Building workspace..."
colcon build --symlink-install --packages-select swarm_sim --cmake-clean-cache --event-handlers console_direct+

# 4. Source Environment
echo "[3/4] Sourcing environment..."
source install/setup.bash

# Export Library Path for SLAM (GTSAM)
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)/install/gtsam/lib:$(pwd)/install/lib

# 5. Launch Simulation
echo "[4/4] Launching Super Simulation..."
echo "Options: 3 Drones, SLAM Enabled"
ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 slam:=true
