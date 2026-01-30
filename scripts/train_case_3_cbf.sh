#!/bin/bash
# Case 3: Training MAPPO with Layered CBF (Control Barrier Functions)
# - Algo='cbf' -> Enables _apply_cbf() in Environment
# - Drones will be actively repelled from boundaries and NFZs by the safety layer.

source /opt/ros/jazzy/setup.bash
source install/setup.bash

echo "=== Case 3: Layered CBF MAPPO Training ==="
echo "Launching with Algo='cbf' (Safety Filter Enabled)"

# 0. Regenerate Map
python3 src/swarm_sim_pkg/swarm_sim/assets/worlds/generate_city.py \
    --output src/swarm_sim_pkg/swarm_sim/assets/worlds/city.sdf \
    --width 250 --length 250 --mode medium

ros2 launch swarm_sim super_simulation.launch.py \
    num_drones:=3 num_stations:=3 slam:=false &
SIM_PID=$!
sleep 15
python3 scripts/spawn_visuals.py

# Run Training
python3 src/swarm_sim_pkg/swarm_sim/training/train_mappo.py \
    --algo cbf \
    --num_drones 3 \
    --iterations 500

kill $SIM_PID
