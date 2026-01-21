#!/bin/bash
set -e

# 1. Clean previous build to ensure fresh state
echo "Cleaning workspace..."
rm -rf /root/ros2_ws/build /root/ros2_ws/install /root/ros2_ws/log

# 2. Source ROS 2 Underlay
source /opt/ros/jazzy/setup.bash

# 3. Build the package
echo "Building swarm_sim..."
cd /root/ros2_ws
colcon build --packages-select swarm_sim --symlink-install

# 4. Source the Overlay
if [ -f "install/setup.bash" ]; then
    source install/setup.bash
else
    echo "Error: install/setup.bash not found!"
    exit 1
fi

# 5. CONSTANTLY FORCE AMENT_PREFIX_PATH
# (This fixes the 'Package not found' error if setup.bash fails to set it correctly)
export AMENT_PREFIX_PATH=/root/ros2_ws/install/swarm_sim:$AMENT_PREFIX_PATH

# 6. Verify Installation
echo "Verifying package..."
if ros2 pkg list | grep -q swarm_sim; then
    echo "Package 'swarm_sim' found."
else
    echo "Error: Package 'swarm_sim' STILL not found in ros2 pkg list."
    echo "AMENT_PREFIX_PATH is: $AMENT_PREFIX_PATH"
    exit 1
fi

# 7. Launch
echo "Launching Simulation..."
ros2 launch swarm_sim simulation.launch.py
