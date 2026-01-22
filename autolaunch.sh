#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=========================================="
echo "   Swarm-Sim Auto-Launcher"
echo "=========================================="

# Ensure ROS 2 is sourced
source /opt/ros/jazzy/setup.bash
echo "Realised by Prince Gedeon"
echo ""

# 1. Fix Git Safety (Redundant but safe)
git config --global --add safe.directory '*'

# 2. Clean Problematic Build Artifacts (Fixes 'Is a directory' error)
echo "[1/4] Cleaning build artifacts..."
rm -rf build/cslam_common_interfaces install/cslam_common_interfaces
# rm -rf build/swarm_sim install/swarm_sim share/swarm_sim
# rm -rf build/ install/ # Uncomment for full clean buffer

# 2. Build Workspace
echo "[2/4] Building workspace..."
# Build Swarm Sim only (SLAM is now in separate container)
colcon build --symlink-install --packages-select swarm_sim --cmake-clean-cache --event-handlers console_direct+

# FIX: Manually move the executable to the expected ROS 2 location
mkdir -p install/swarm_sim/lib/swarm_sim
cp install/swarm_sim/bin/tf_broadcaster install/swarm_sim/lib/swarm_sim/

# 4. Source Environment
echo "[3/4] Sourcing environment..."
source install/local_setup.bash
# Fallback: Manually add to path if setup.bash fails (Container Issue)
export AMENT_PREFIX_PATH=$AMENT_PREFIX_PATH:$(pwd)/install/swarm_sim
export PYTHONPATH=$PYTHONPATH:$(pwd)/install/swarm_sim/lib/python3.12/site-packages

# Export Library Path for SLAM (GTSAM)
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)/install/gtsam/lib:$(pwd)/install/lib

# 5. Launch Simulation
echo "[4/4] Launching Super Simulation..."
echo "Options: 3 Drones, SLAM External"
ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 slam:=false
