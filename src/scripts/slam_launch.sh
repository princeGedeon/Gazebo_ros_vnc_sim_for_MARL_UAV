#!/bin/bash
set -e

# This script is meant to be run INSIDE the SLAM container (rosette_slam)
# cmd: docker exec -it rosette_slam bash src/scripts/slam_launch.sh

echo "Starting Multi-Robot SLAM (mrg_slam)..."
source /opt/ros/jazzy/setup.bash
source /home/ubuntu/ros2_ws/install/setup.bash

# Ensure we can see the robots
# The mrg_slam package is installed in the image at /root/ros2_ws/install (or similar)
# Actually, aserbremen's image has it pre-installed.
# We just need to launch it.

# Launch for 3 UAVs
# We use background jobs to launch multiple instances
echo "Launching SLAM for uav_0..."
ros2 launch mrg_slam mrg_slam.launch.py model_namespace:=uav_0 use_sim_time:=true x:=0.0 y:=0.0 z:=0.0 &
PID0=$!

echo "Launching SLAM for uav_1..."
ros2 launch mrg_slam mrg_slam.launch.py model_namespace:=uav_1 use_sim_time:=true x:=5.0 y:=0.0 z:=0.0 &
PID1=$!

echo "Launching SLAM for uav_2..."
ros2 launch mrg_slam mrg_slam.launch.py model_namespace:=uav_2 use_sim_time:=true x:=-5.0 y:=0.0 z:=0.0 &
PID2=$!

echo "SLAM nodes started. Press Ctrl+C to stop all."
wait $PID0 $PID1 $PID2
