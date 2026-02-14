#!/bin/bash
set -e

# ==============================================================================
# 🎮 MASTER LAUNCH SCRIPT FOR WSL (NO AUTOLAUNCH)
# ==============================================================================

# 1. Source Environments
echo "🔄 Sourcing environments..."
source /opt/ros/jazzy/setup.bash
if [ -d "install" ]; then
    source install/setup.bash
else
    echo "❌ Error: 'install' directory not found. Did you run './install_linux.sh'?"
    exit 1
fi
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# 2. Cleanup Old Processes
echo "🧹 Cleaning previous simulation processes..."
pkill -f gazebo || true
pkill -f gz || true
pkill -f python3 || true
pkill -f ros2 || true
pkill -f rviz2 || true
sleep 2

# 3. Environment Variables (WSL Fixes)
echo "🔧 Configuring WSL Environment..."
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=all
export GZ_IP=127.0.0.1
export GZ_PARTITION=sim_partition

# 4. Check Compilation (Brief)
if [ ! -d "install/swarm_sim" ]; then
    echo "⚙️ Building workspace..."
    colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
    source install/setup.bash
fi

# 5. Launch Simulation (Background)
# Note: super_simulation.launch.py handles World Generation -> Gazebo -> RViz
echo "🚀 Launching Simulation Stack (Gazebo + RViz)..."
ros2 launch swarm_sim super_simulation.launch.py \
    num_drones:=3 \
    slam:=true \
    map_type:=world \
    map_file:=generated_city.sdf \
    > /tmp/gazebo_sim.log 2>&1 &

PID_SIM=$!
echo "⏳ Waiting 10s for Gazebo to initialize..."
sleep 10

# 6. Check if Simulation is Alive
if ps -p $PID_SIM > /dev/null; then
    echo "✅ Simulation running (PID: $PID_SIM)"
    echo "   Logs at: /tmp/gazebo_sim.log"
else
    echo "❌ Simulation failed to start! Check logs."
    cat /tmp/gazebo_sim.log
    exit 1
fi

# 7. Launch Training (Foreground)
echo "🧠 Starting Training (MAPPO)..."
echo "   (Press Ctrl+C to stop everything)"

# Trap Ctrl+C to kill simulation too
trap "echo '🛑 Stopping all processes...'; kill $PID_SIM; pkill -f gazebo; pkill -f python3; exit" SIGINT SIGTERM

python3 src/swarm_sim_pkg/swarm_sim/training/train_mappo.py \
    --num-drones 3 \
    --total-timesteps 1000000 \
    --no-gui

echo "✅ Training Completed."
