#!/bin/bash
# DEBUG SCRIPT FOR WSL GAZEBO/ROS2
set -e

echo "🔍 Starting WSL Diagnostic..."

# 1. Environment Check
echo "--------------------------------"
echo "1. Checking Environment..."
if [ -z "$ROS_DISTRO" ]; then
    echo "❌ ROS_DISTRO not set. Sourcing /opt/ros/jazzy/setup.bash..."
    source /opt/ros/jazzy/setup.bash
else
    echo "✅ ROS_DISTRO: $ROS_DISTRO"
fi

# 2. Check Graphics
echo "--------------------------------"
echo "2. Checking Graphics (glxinfo)..."
if command -v glxinfo &> /dev/null; then
    glxinfo | grep "OpenGL version" || echo "❌ OpenGL not found"
else
    echo "⚠️ glxinfo not found (install mesa-utils if possible)"
fi
echo "DISPLAY: $DISPLAY"
echo "LIBGL_ALWAYS_SOFTWARE: $LIBGL_ALWAYS_SOFTWARE"

# 3. Test Gazebo Server (Headless)
echo "--------------------------------"
echo "3. Testing Gazebo Server (Headless)..."
echo "   Launching 'gz sim -s -v 4 -r shapes.sdf' for 5 seconds..."
timeout 5s gz sim -s -v 4 -r shapes.sdf &
PID_GZ=$!
sleep 6
if ps -p $PID_GZ > /dev/null; then
    echo "✅ Gazebo Server is running!"
    kill $PID_GZ
else
    echo "❌ Gazebo Server crashed or failed to start."
fi

# 4. Test Gazebo GUI
echo "--------------------------------"
echo "4. Testing Gazebo GUI..."
echo "   Launching 'gz sim -g -v 4 shapes.sdf' for 5 seconds..."
echo "   (Check your taskbar/window manager)"
timeout 5s gz sim -g -v 4 shapes.sdf &
PID_GUI=$!
sleep 6
if ps -p $PID_GUI > /dev/null; then
    echo "✅ Gazebo GUI process is running (did you see a window?)"
    kill $PID_GUI
else
    echo "❌ Gazebo GUI crashed immediately."
fi

# 5. Check RViz Dependencies
echo "--------------------------------"
echo "5. Checking RViz Plugins..."
if [ -f /opt/ros/jazzy/share/rviz_default_plugins/package.xml ]; then
    echo "✅ rviz_default_plugins found."
else
    echo "❌ rviz_default_plugins NOT found! (Try: sudo apt install ros-jazzy-rviz-default-plugins)"
fi

echo "--------------------------------"
echo "Diagnostic Complete."
