
#!/bin/bash
source /opt/ros/jazzy/setup.bash
cd /root/ros2_ws
colcon build --packages-select swarm_sim --symlink-install
source install/setup.bash
export AMENT_PREFIX_PATH=$PWD/install/swarm_sim:$AMENT_PREFIX_PATH

# Validate
echo "Swarm Sim Package Installed."
ros2 pkg list | grep swarm_sim

# Launch
# ros2 launch swarm_sim simulation.launch.py
