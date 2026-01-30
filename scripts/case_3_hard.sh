#!/bin/bash
# Case 3: Hard / Large Scale
# 5 Drones, 5 Stations, 5 NFZ

source /opt/ros/jazzy/setup.bash
source install/setup.bash

echo "Starting Case 3: Hard/Large Setup..."
echo " - 5 Drones"
echo " - 5 Stations"
echo " - 5 NFZ (Visuals might only show 3 from default script)"

# Launch Simulation
ros2 launch swarm_sim super_simulation.launch.py \
    num_drones:=5 \
    num_stations:=5 \
    map_file:=city.sdf \
    slam:=true &
SIM_PID=$!

sleep 15
python3 scripts/spawn_visuals.py

wait $SIM_PID
