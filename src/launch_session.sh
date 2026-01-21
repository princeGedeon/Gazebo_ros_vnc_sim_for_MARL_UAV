#!/bin/bash
# Helper to launch simulation with specific maps easily inside Docker

MAP_NAME=$1
NUM_DRONES=${2:-3}

if [ -z "$MAP_NAME" ]; then
    echo "Usage: ./launch_session.sh [map_name] [num_drones]"
    echo "Available Maps (Examples):"
    echo "  - city       (Default procedural city)"
    echo "  - Acourse    (Competition Track A)"
    echo "  - Bcourse    (Competition Track B)"
    echo "  - 3m_wall    (Simple Wall)"
    echo "  - kepco      (Warehouse)"
    exit 1
fi

# 1. Check if it's the default city
if [ "$MAP_NAME" == "city" ]; then
    echo "Launching Default City..."
    ros2 launch swarm_sim multi_ops.launch.py num_drones:=$NUM_DRONES
    exit 0
fi

# 2. Search for the map in external_maps
# We assume the container path /root/ros2_ws/src/...
SEARCH_DIR="/root/ros2_ws/src/swarm_sim_pkg/swarm_sim/assets/external_maps"
FOUND_PATH=$(find $SEARCH_DIR -name "$MAP_NAME" -type d | head -n 1)

if [ -z "$FOUND_PATH" ]; then
    echo "Error: Map '$MAP_NAME' not found in assets."
    exit 1
fi

MODEL_FILE="$FOUND_PATH/model.sdf"

if [ ! -f "$MODEL_FILE" ]; then
    echo "Error: Found directory $FOUND_PATH, but no model.sdf inside."
    exit 1
fi

echo "Found Map: $MAP_NAME at $MODEL_FILE"
echo "Launching..."

# Launch in 'model' mode (spawns empty world + the map model)
ros2 launch swarm_sim multi_ops.launch.py \
    num_drones:=$NUM_DRONES \
    map_type:=model \
    map_file:="$MODEL_FILE"
