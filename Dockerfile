FROM osrf/ros:jazzy-desktop-full

USER root

# Avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install core tools, VNC, and window manager
RUN apt-get update && apt-get install -y \
    supervisor \
    xfce4 \
    xfce4-goodies \
    xvfb \
    x11vnc \
    net-tools \
    novnc \
    novnc \
    wget \
    curl \
    git \
    nano \
    python3-pip \
    mesa-utils \
    libgl1-mesa-dri \
    libgl1 \
    dbus-x11 \
    vulkan-tools \
    && rm -rf /var/lib/apt/lists/*

# Manually remove Debian python packages that conflict with Pip
# (We do this instead of apt-remove to avoid deleting ROS 2)

RUN rm -rf /usr/lib/python3/dist-packages/typing_extensions* \
    /usr/lib/python3/dist-packages/numpy* \
    /usr/lib/python3/dist-packages/mpmath* \
    /usr/lib/python3/dist-packages/packaging* \
    /usr/lib/python3/dist-packages/blinker* \
    /usr/lib/python3/dist-packages/kiwisolver*

RUN pip3 install --break-system-packages \
    gymnasium \
    websockify \
    pettingzoo \
    stable-baselines3 \
    numpy \
    matplotlib \
    pillow \
    "ray[rllib]" \
    torch \
    supersuit \
    shimmy \
    scipy \
    open3d

# Install Real SLAM Dependencies (Boost, PCL, Octomap)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libboost-all-dev \
    libpcl-dev \
    libgoogle-glog-dev \
    ros-jazzy-octomap-ros \
    ros-jazzy-octomap-server \
    ros-jazzy-pcl-ros \
    ros-jazzy-ros-gz \
    ros-jazzy-rtabmap-msgs \
    ros-jazzy-nav2-msgs \
    ros-jazzy-rtabmap-conversions \
    ros-jazzy-teleop-twist-keyboard \
    && rm -rf /var/lib/apt/lists/*

# Build GTSAM (From Source - System Libs Missing in Jazzy Repo sometimes)
RUN git clone https://github.com/borglab/gtsam.git /tmp/gtsam && \
    cd /tmp/gtsam && \
    mkdir build && cd build && \
    cmake -DGTSAM_USE_SYSTEM_EIGEN=ON -DGTSAM_BUILD_TESTS=OFF -DGTSAM_BUILD_EXAMPLES=OFF .. && \
    make -j4 install && \
    rm -rf /tmp/gtsam

# Build TEASER++
RUN git clone https://github.com/MIT-SPARK/TEASER-plusplus.git /tmp/teaser && \
    cd /tmp/teaser && \
    # Patch for GCC 13 (Ubuntu 24.04) - Dynamically find the file
    find . -name "tinyply.h" -exec sed -i '1i #include <cstdint>' {} + && \
    pip3 install --break-system-packages . && \
    rm -rf /tmp/teaser

# Setup VNC and Supervisor
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Setup Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Environment variables
ENV DISPLAY=:1
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=all

# Expose ports (VNC and NoVNC)
EXPOSE 5901 6080

WORKDIR /root/ros2_ws
COPY . /root/ros2_ws/

# Pre-build the workspace
RUN . /opt/ros/jazzy/setup.sh && \
    colcon build || echo "Build failed, user can fix later"

ENTRYPOINT ["/entrypoint.sh"]

# Add source to bashrc for interactive shells
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "if [ -f /root/ros2_ws/install/setup.bash ]; then source /root/ros2_ws/install/setup.bash; fi" >> /root/.bashrc

