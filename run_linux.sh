#!/bin/bash
set -e

# Source environments
source /opt/ros/jazzy/setup.bash
if [ -d "venv" ]; then
    source venv/bin/activate
fi
source install/setup.bash

# Ensure NVIDIA vars if present (for native GPU)
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=all

# Auto-Source Environment (Relative Path)
if [ -f "install/setup.bash" ]; then
    source install/setup.bash
fi

# Aggressive Cleanup (Kill old Gazebo/ROS processes)
echo "🧹 Cleaning previous simulation processes..."
pkill -f gazebo || true
pkill -f gz || true
pkill -f python3 || true
pkill -f ros2 || true
pkill -f rviz2 || true

echo "🚁 Starting Simulation..."
echo "   Mode: Native Linux"

# Launch main script
./scripts/autolaunch_full.sh case_1 "$@"
