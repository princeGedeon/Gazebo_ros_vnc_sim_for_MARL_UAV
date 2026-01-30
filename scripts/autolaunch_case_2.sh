#!/bin/bash
# autolaunch_case_2.sh
# Automates the "Split Terminal" workflow for Case 2 (Lagrange)

echo "=== Case 2: Automated Split Launch (Lagrange) ==="

# 0. Regenerate Map
echo "[1/3] Regenerating City..."
python3 src/swarm_sim_pkg/swarm_sim/assets/worlds/generate_city.py \
    --output src/swarm_sim_pkg/swarm_sim/assets/worlds/city.sdf \
    --width 250 --length 250 --mode medium

# 1. Launch Simulation (New Terminal)
echo "[2/3] Launching Simulation in New Terminal..."

if command -v gnome-terminal &> /dev/null; then
    gnome-terminal --title="Swarm Sim (Case 2: Lagrange)" -- bash -c "ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 slam:=true octomap:=true; exec bash"
elif command -v x-terminal-emulator &> /dev/null; then
    x-terminal-emulator -e "bash -c 'ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 slam:=true octomap:=true; exec bash'"
else
    echo "⚠️  No GUI Terminal found. Launching in background."
    ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 slam:=true octomap:=true &
fi

echo "Waiting 15s for Sim to load..."
sleep 15
python3 scripts/spawn_visuals.py

# 2. Launch Training (Current Terminal)
echo "[3/3] Launching Training (Follow Logs Here)..."
python3 src/swarm_sim_pkg/swarm_sim/training/train_mappo.py \
    --algo lagrangian \
    --num_drones 3 \
    --iterations 500
