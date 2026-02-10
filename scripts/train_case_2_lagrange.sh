#!/bin/bash
# Case 2: Training MAPPO with Lagrangian Constraints
# - Algo='lagrangian' (Tracks 'cost' in info for constraint updates)
# - Note: Simple implementation uses standard PPO but labels run as Lagrangian for monitoring cost signal.

source /opt/ros/jazzy/setup.bash
source install/setup.bash

echo "=== Case 2: Lagrangian MAPPO Training ==="
echo "Launching with Algo='lagrangian'"


# 0. Regenerate Map (Ensure consistency with User Config)
# This overrides 'city.sdf' with the 'urban_city_rich' definition
python3 src/swarm_sim_pkg/swarm_sim/assets/worlds/generate_city.py \
    --output src/swarm_sim_pkg/swarm_sim/assets/worlds/city.sdf \
    --width 250 --length 250 --mode medium

# 1. Launch Sim (Background)
# 1. Launch Sim (Background)
# Full Stack: Gazebo + SLAM (Graph) + OctoMap (3D) + RViz
ros2 launch swarm_sim super_simulation.launch.py \
    num_drones:=3 \
    num_stations:=3 \
    slam:=true \
    octomap:=true &
SIM_PID=$!
sleep 15
python3 scripts/spawn_visuals.py

# 2. Run Training
python3 src/swarm_sim_pkg/swarm_sim/training/train_mappo_lagrangian.py \
    --num-drones 3 \
    --iterations 500

kill $SIM_PID
