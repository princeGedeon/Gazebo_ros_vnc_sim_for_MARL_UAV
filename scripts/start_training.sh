#!/bin/bash

# Source ROS 2 (Adjust if needed for Jazzy/Humble)
if [ -f /opt/ros/jazzy/setup.bash ]; then
    source /opt/ros/jazzy/setup.bash
elif [ -f /opt/ros/humble/setup.bash ]; then
    source /opt/ros/humble/setup.bash
fi

# Source Workspace
if [ -f install/setup.bash ]; then
    source install/setup.bash
fi

# Ensure Python path includes the package
export PYTHONPATH=$PYTHONPATH:$(pwd)/src/swarm_sim_pkg

echo "[Training] Starting MAPPO Training with NFZ & Altitude Constraints..."
echo "[Training] Visualizations configured for RViz (Markers)."

# Run the training script
python3 src/swarm_sim_pkg/swarm_sim/training/train_mappo.py
