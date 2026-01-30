#!/bin/bash
# autolaunch_case_1.sh
# Automates the "Split Terminal" workflow for Case 1
# Curriculum Level 1: Small City (120x120m), Low Density.

echo "=== Case 1: Automated Split Launch (Curriculum: Easy) ==="

# 0. Regenerate Map (Curriculum: Small & Simple)
echo "[1/3] Regenerating City (Small 120x120m)..."
python3 src/swarm_sim_pkg/swarm_sim/assets/worlds/generate_city.py \
    --output src/swarm_sim_pkg/swarm_sim/assets/worlds/city.sdf \
    --width 120 --length 120 --mode low

# 1. Launch Simulation (New Terminal)
echo "[2/3] Launching Simulation in New Terminal..."

# Try gnome-terminal
if command -v gnome-terminal &> /dev/null; then
    # Note: We launch spawn_visuals inside the simulation window logic if possible, 
    # but since spawn_visuals depends on sim being ready, we keep it separate here.
    gnome-terminal --title="Swarm Simulation (Gazebo+RViz)" -- bash -c "ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 slam:=true; exec bash"
elif command -v x-terminal-emulator &> /dev/null; then
    x-terminal-emulator -e "bash -c 'ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 slam:=true; exec bash'"
else
    echo "⚠️  No GUI Terminal found (gnome-terminal/x-terminal-emulator)."
    echo "    Reverting to background launch (Logs will mix!)."
    ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 slam:=true &
fi

echo "Waiting 15s for Sim to load..."
sleep 15

# Spawn Visuals
python3 scripts/spawn_visuals.py

# 2. Launch Training (Current Terminal)
echo "[3/3] Launching Training (Follow Logs Here)..."
python3 src/swarm_sim_pkg/swarm_sim/training/train_mappo.py \
    --algo simple \
    --num_drones 3 \
    --iterations 500
