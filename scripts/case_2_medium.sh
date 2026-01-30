#!/bin/bash
# Case 2: Medium (Requested Configuration)
# 3 Drones, 3 Stations (Spaced), 3 NFZ, Medium City

source /opt/ros/jazzy/setup.bash
source install/setup.bash

echo "Starting Case 2: Medium Setup..."
echo " - 3 Drones (Spaced)"
echo " - 3 Stations (Spaced)"
echo " - 3 NFZ (Visualized in Red)"
echo " - Medium City Environment"

# 1. Launch Simulation in Background
ros2 launch swarm_sim super_simulation.launch.py \
    num_drones:=3 \
    num_stations:=3 \
    map_file:=city.sdf \
    slam:=true &
SIM_PID=$!

# 2. Wait for Gazebo to load (15s)
echo "Waiting for Gazebo to start..."
sleep 15

# 3. Spawn Visuals (NFZ Cylinders)
echo "Spawning Visual Markers..."
python3 scripts/spawn_visuals.py

# 4. Wait for Sim to exit
wait $SIM_PID
