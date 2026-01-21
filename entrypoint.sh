#!/bin/bash
set -e

# Setup ROS 2 environment
source /opt/ros/jazzy/setup.bash

# Fix Git Safety (Dubious Ownership in Container)
git config --global --add safe.directory '*'

# Check for custom workspace
if [ -f "/root/ros2_ws/install/setup.bash" ]; then
    source /root/ros2_ws/install/setup.bash
    # Fix overlay issue where package isn't found
    export AMENT_PREFIX_PATH=/root/ros2_ws/install/swarm_sim:$AMENT_PREFIX_PATH
fi

# GPU Rendering Configuration
export RENDERING_MODE=${RENDERING_MODE:-gpu}

if [ "$RENDERING_MODE" = "gpu" ]; then
    echo "Configuring for GPU Rendering (NVIDIA)..."
    export __NV_PRIME_RENDER_OFFLOAD=1
    export __GLX_VENDOR_LIBRARY_NAME=nvidia
    export NVIDIA_DRIVER_CAPABILITIES=all
    export NVIDIA_VISIBLE_DEVICES=all
    
    # Ensure nvidia libs are found first if they are in a standard mount location
    # Sometimes container runtime puts them in /usr/lib/x86_64-linux-gnu directly, which is fine.
else
    echo "Configuring for CPU Rendering (Software)..."
    export LIBGL_ALWAYS_SOFTWARE=1
fi

# Check GUI Mode
export GUI=${GUI:-vnc}

if [ "$GUI" = "host" ]; then
    echo "---------------------------------------------------"
    echo "   Running in NATIVE HOST MODE (X11 Forwarding)"
    echo "   Make sure you ran 'xhost +local:root' on host."
    echo "---------------------------------------------------"
    # Keep container alive so user can exec into it
    exec tail -f /dev/null
else
    echo "Starting VNC and ROS 2 environment..."
    exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
fi
