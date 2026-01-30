#!/bin/bash

# Master Launch Script for Swarm Coverage
# Launches Simulation in background and then Training/control script.

echo ">>> Starting Gazebo Simulation Environment..."
# Run the super_simulation in background
ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 map_file:=city.sdf open_rviz:=true slam:=true &
SIM_PID=$!

echo "Waiting for Simulation to stabilize (15s)..."
sleep 15

echo ">>> Starting RL Training / Control Node..."
# Run the Python training script
# Ensure we are in the project root (User runs ./scripts/launch_all.sh or cd scripts; ./launch_all.sh)
cd "$(dirname "$0")/.."

# Check if we should run training or just a test
if [ "$1" == "train" ]; then
    python3 src/swarm_sim_pkg/swarm_sim/training/train_mappo.py
else
    echo "Usage: ./launch_all.sh train"
    echo "Running dry-run check..."
    python3 -c "import rclpy; print('ROS2 Python works')"
fi

echo ">>> Stopping Simulation..."
kill $SIM_PID
