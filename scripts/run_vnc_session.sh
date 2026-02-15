#!/bin/bash
set -e

# 1. Kill old VNC sessions
echo "🧹 Cleaning old VNC sessions..."
vncserver -kill :1 || true
rm -rf /tmp/.X11-unix/X1
rm -rf /tmp/.X1-lock

# 2. Start VNC Server geometry 1920x1080
echo "🚀 Starting VNC Server on :1 (Port 5901)..."
vncserver :1 -geometry 1280x720 -depth 24

export DISPLAY=:1
export GZ_IP=127.0.0.1
export GZ_PARTITION=sim_partition

echo "✅ VNC Started!"
echo "👉 Connect with RealVNC Viewer to: localhost:5901"
echo "   Password: password"
echo ""

# 3. Ask to launch Gazebo
read -p "🚀 Launch Gazebo inside VNC now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./run_linux.sh
fi
