#!/bin/bash
set -e

echo "🚀 Starting Native Installation for Gazebo Swarm Sim..."

# 1. Check OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [ "$VERSION_ID" != "24.04" ]; then
        echo "⚠️  WARNING: This script is designed for Ubuntu 24.04 (Noble)."
        echo "    Detected: $PRETTY_NAME"
        read -p "    Press ENTER to continue anyway, or Ctrl+C to cancel."
    fi
fi

# 2. Install System Dependencies
echo "📦 Installing System Dependencies..."
sudo apt-get update
sudo apt-get install -y \
    supervisor xfce4 xfce4-goodies xvfb x11vnc net-tools novnc wget curl git nano \
    python3-pip python3-venv mesa-utils libgl1-mesa-dri libgl1 dbus-x11 vulkan-tools \
    build-essential cmake libboost-all-dev libpcl-dev libgoogle-glog-dev python3-scipy \
    ros-jazzy-sensor-msgs ros-jazzy-sensor-msgs-py ros-jazzy-octomap-ros \
    ros-jazzy-octomap-server ros-jazzy-pcl-ros ros-jazzy-ros-gz ros-jazzy-rtabmap-msgs \
    ros-jazzy-nav2-msgs ros-jazzy-rtabmap-conversions ros-jazzy-teleop-twist-keyboard \
    python3-vcstool libg2o-dev libsuitesparse-dev libgeographiclib-dev \
    ros-jazzy-geodesy ros-jazzy-nmea-msgs

# 3. Python Environment
echo "🐍 Setting up Python Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install specific pip versions (matches Dockerfile)
pip install --upgrade pip
pip install -r requirements.txt

# 4. Clone Missing Repos
echo "📥 Checking source repositories..."

# Multi-Robot-Graph-SLAM
if [ ! -f "src/Multi-Robot-Graph-SLAM/mrg_slam.repos" ]; then
    echo "   Cloning Multi-Robot-Graph-SLAM..."
    rm -rf src/Multi-Robot-Graph-SLAM
    git clone https://github.com/aserbremen/Multi-Robot-Graph-SLAM src/Multi-Robot-Graph-SLAM
fi

# PX4-gazebo-models
if [ ! -d "src/swarm_sim_pkg/swarm_sim/assets/PX4-gazebo-models/.git" ]; then
    echo "   Cloning PX4-gazebo-models..."
    rm -rf src/swarm_sim_pkg/swarm_sim/assets/PX4-gazebo-models
    git clone https://github.com/PX4/PX4-gazebo-models src/swarm_sim_pkg/swarm_sim/assets/PX4-gazebo-models
fi

# 5. VCS Import
echo "🔄 Importing dependencies via vcstool..."
if [ -f "src/Multi-Robot-Graph-SLAM/mrg_slam.repos" ]; then
    vcs import src < src/Multi-Robot-Graph-SLAM/mrg_slam.repos || echo "⚠️ vcs import had issues, check output."
else
    echo "⚠️ mrg_slam.repos not found, skipping vcs import."
fi

# 6. Build Workspace
echo "🔨 Building ROS 2 Workspace..."
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --parallel-workers 1

echo "✅ Installation Complete!"
echo "   Run './run_linux.sh' to start the simulation."
