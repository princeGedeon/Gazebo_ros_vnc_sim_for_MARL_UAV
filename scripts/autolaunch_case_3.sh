#!/bin/bash
# autolaunch_case_3.sh
# Automates the "Split Terminal" workflow for Case 3 (Layered CBF)

echo "=== Case 3: Automated Split Launch (CBF) ==="

# 0. Regenerate Map
echo "[1/3] Regenerating City..."
python3 src/swarm_sim_pkg/swarm_sim/assets/worlds/generate_city.py \
    --output src/swarm_sim_pkg/swarm_sim/assets/worlds/city.sdf \
    --width 250 --length 250 --mode medium

# 1. Launch Simulation (New Terminal)
echo "[2/3] Launching Simulation in New Terminal..."

# Note: Enabling SLAM for Case 3 as requested for verification, even if original script had it false.
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal --title="Swarm Sim (Case 3: CBF)" -- bash -c "ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 slam:=true; exec bash"
elif command -v x-terminal-emulator &> /dev/null; then
    x-terminal-emulator -e "bash -c 'ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 slam:=true; exec bash'"
else
    echo "⚠️  No GUI Terminal found. Launching in background."
    ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 slam:=true &
fi

echo "Waiting 15s for Sim to load..."
sleep 15
python3 scripts/spawn_visuals.py

# 2. Launch Training (Current Terminal)
echo "[3/3] Launching Training (Follow Logs Here)..."
python3 src/swarm_sim_pkg/swarm_sim/training/train_mappo.py \
    --algo cbf \
    --num_drones 3 \
    --iterations 500
