#!/bin/bash
set -e

# Source environments
source /opt/ros/jazzy/setup.bash
if [ -d "venv" ]; then
    source venv/bin/activate
fi
source install/setup.bash

# Ensure NVIDIA vars if present (for native GPU)
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=all

echo "🚁 Starting Simulation..."
echo "   Mode: Native Linux"

# Launch main script
./scripts/autolaunch_full.sh case_1
