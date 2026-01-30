#!/bin/bash
# scripts/clean_storage.sh
# Deletes temporary files, checkpoints, and caches to free up disk space.

echo "🧹 Cleaning Storage..."

# 1. RL Checkpoints (Massive)
if [ -d "rllib_results" ]; then
    echo " -> Removing rllib_results/ (Training Checkpoints)..."
    rm -rf rllib_results/*
fi

# 2. Python Cache
echo " -> Removing __pycache__ folders..."
find . -type d -name "__pycache__" -exec rm -rf {} +

# 3. Old Map Outputs
if [ -d "outputs" ]; then
    echo " -> Removing outputs/*.laz (Old Maps)..."
    rm -f outputs/*.laz
    rm -f outputs/*.npy
fi

# 4. Colcon Build Artifacts (Local, not Docker)
# If user wants to clean local build too:
# rm -rf build/ install/ log/

echo "✅ Storage Cleaned."
