#!/bin/bash
# Case 1: Training Standard MAPPO (Simple PPO)
# - No special safety layers, standard penalties.
# - Workspace visual markers provided.

source /opt/ros/jazzy/setup.bash
source install/setup.bash

echo "=== Case 1: Simple MAPPO Training ==="
echo "Launching Simulation + Training with Algo='simple'"

# 0. Regenerate Map
python3 src/swarm_sim_pkg/swarm_sim/assets/worlds/generate_city.py \
    --output src/swarm_sim_pkg/swarm_sim/assets/worlds/city.sdf \
    --width 250 --length 250 --mode medium

# 1. Launch Sim (Background)
# We use case 2 setup (Medium) as the base environment
# 1. Launch Sim (Background)
# Full Stack: Gazebo + SLAM (Graph) + OctoMap (3D) + RViz
ros2 launch swarm_sim super_simulation.launch.py \
    num_drones:=3 \
    num_stations:=3 \
    slam:=true \
    octomap:=true &

SIM_PID=$!
sleep 15

# Spawn Visuals
python3 scripts/spawn_visuals.py

# 2. Run Training
python3 src/swarm_sim_pkg/swarm_sim/training/train_mappo.py \
    --algo simple \
    --num-drones 3 \
    --iterations 500

# Cleanup
kill $SIM_PID
