#!/bin/bash
# Case 1: Easy / Discovery
# 1 Drone, 1 Station, No NFZ, Small Area

source /opt/ros/jazzy/setup.bash
source install/setup.bash

echo "Starting Case 1: Easy Setup..."
echo " - 1 Drone"
echo " - 1 Station"
echo " - No NFZ"

# Launch Simulation
ros2 launch swarm_sim super_simulation.launch.py \
    num_drones:=1 \
    num_stations:=1 \
    map_file:=city.sdf \
    slam:=true
