#!/bin/bash
source /opt/ros/jazzy/setup.bash
source /root/ros2_ws/install/setup.bash
export AMENT_PREFIX_PATH=/root/ros2_ws/install/swarm_sim:$AMENT_PREFIX_PATH
echo "AMENT: $AMENT_PREFIX_PATH"
ros2 pkg list | grep swarm_sim
