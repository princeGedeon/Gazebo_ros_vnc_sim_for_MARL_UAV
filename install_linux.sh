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

# 2. Check & Install ROS 2 Jazzy
if [ ! -f /opt/ros/jazzy/setup.bash ]; then
    echo "⚠️ ROS 2 Jazzy not found. Installing now (requires sudo)..."
    
    # 2.1 Enable Universe
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository universe
    
    # 2.2 Add Key & Repo
    sudo apt-get update && sudo apt-get install -y curl
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
    
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
    
    # 2.3 Install
    sudo apt-get update
    sudo apt-get install -y ros-jazzy-desktop-full python3-colcon-common-extensions
    
    echo "✅ ROS 2 Jazzy Installed!"
else
    echo "✅ ROS 2 Jazzy already installed."
fi

# 3. Install System Dependencies
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
# Ensure venv is created completely
rm -rf venv
python3 -m venv venv

if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Error: Failed to create venv. 'python3-venv' might still be missing."
    exit 1
fi

# Prevent colcon from building the venv
touch venv/COLCON_IGNORE

source venv/bin/activate

# Install specific pip versions (matches Dockerfile)
echo "📦 Installing Python dependencies (Torch, Ray, etc.)..."
echo "⚠️  This involves downloading ~2GB of data. It may take 10-20 minutes."
echo "    Please wait... (I enabled logs so you can see progress)"
pip install --upgrade pip
pip install -r requirements.txt -v

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

# Clean previous build artifacts (Fixes layout mismatch errors between Windows/Linux)
echo "🧹 Cleaning previous build artifacts..."
rm -rf build install log

colcon build --symlink-install --parallel-workers 1 --event-handlers console_direct+ --base-paths src

echo "✅ Installation Complete!"
echo "   Run './run_linux.sh' to start the simulation."
