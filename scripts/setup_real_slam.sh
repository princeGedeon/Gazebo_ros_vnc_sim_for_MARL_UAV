#!/bin/bash
set -e

echo "=========================================="
echo "   Swarm-SLAM Real Stack Installer"
echo "=========================================="
echo "This script installs system dependencies (Boost, GTSAM, PCL) and builds the SLAM stack."
echo "Requires SUDO access."
echo ""

# 1. System Dependencies (The stuff missing in the container)
echo "[1/5] Installing System Dependencies (Boost, GTSAM, PCL)..."
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-pip \
    python3-vcstool \
    libboost-all-dev \
    libgtsam-dev \
    libgtsam-unstable-dev \
    libpcl-dev \
    libgoogle-glog-dev \
    ros-jazzy-octomap-ros \
    ros-jazzy-octomap-server \
    ros-jazzy-pcl-ros

# 2. Python Deps
echo "[2/5] Installing Python Libraries..."
# Check if requirements exist in new location
if [ -f "src/swarm_slam_stack/requirements.txt" ]; then
    pip3 install --break-system-packages -r src/swarm_slam_stack/requirements.txt || echo "Warning: pip install had issues."
else
    echo "Requirements file not found in src/swarm_slam_stack/. Skipping."
fi

# 3. Teaser++ (If not built)
if [ ! -d "src/external_libs/TEASER-plusplus/build" ]; then
    echo "[3/5] Building TEASER++..."
    # Clone if not present (though we expect it moved)
    if [ ! -d "src/external_libs/TEASER-plusplus" ]; then
         git clone https://github.com/MIT-SPARK/TEASER-plusplus.git src/external_libs/TEASER-plusplus
    fi
    cd src/external_libs/TEASER-plusplus
    pip3 install --break-system-packages .
    cd ../../../..
else
    echo "[3/5] TEASER++ seems to be present. Skipping."
fi

# 4. Swarm-SLAM Workspace
echo "[4/5] Building Swarm-SLAM Workspace..."
# Ensure we have the repos
if [ -d "src/swarm_slam_stack" ]; then
    cd src/swarm_slam_stack
    vcs import . < cslam.repos || echo "Repos already imported"
    cd ../..
    
    # Build
    source /opt/ros/jazzy/setup.bash
    colcon build --packages-up-to cslam_experiments \
        --cmake-args -DCMAKE_BUILD_TYPE=Release
else
    echo "Error: src/swarm_slam_stack not found!"
fi


echo "=========================================="
echo "   Installation Complete!"
echo "=========================================="
echo "To run Real SLAM:"
echo "1. source install/setup.bash"
echo "2. ros2 launch swarm_sim swarm_slam.launch.py"
