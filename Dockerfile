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
    /usr/lib/python3/dist-packages/kiwisolver* \
    /usr/lib/python3/dist-packages/zipp*

RUN pip3 install --no-cache-dir --break-system-packages \
    gymnasium \
    websockify \
    pettingzoo \
    stable-baselines3 \
    "ray[rllib,default]" \
    "numpy<2.0.0" \
    torch \
    supersuit \
    shimmy \
    scipy \
    open3d \
    numba \
    scikit-learn

# Install Real SLAM Dependencies (Boost, PCL, Octomap)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libboost-all-dev \
    libpcl-dev \
    libgoogle-glog-dev \
    python3-scipy \
    ros-jazzy-sensor-msgs \
    ros-jazzy-sensor-msgs-py \
    ros-jazzy-octomap-ros \
    ros-jazzy-octomap-server \
    ros-jazzy-pcl-ros \
    ros-jazzy-ros-gz \
    ros-jazzy-rtabmap-msgs \
    ros-jazzy-nav2-msgs \
    ros-jazzy-rtabmap-conversions \
    ros-jazzy-teleop-twist-keyboard \
    python3-vcstool \
    libg2o-dev \
    libsuitesparse-dev \
    libgeographiclib-dev \
    ros-jazzy-geodesy \
    ros-jazzy-nmea-msgs \
    && rm -rf /var/lib/apt/lists/*


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
# Expose ports (VNC, NoVNC, Ray Dashboard 8265)
EXPOSE 5901 6080 8265

WORKDIR /root/ros2_ws
COPY . /root/ros2_ws/

# Pre-build the workspace
# Import dependencies automatically
RUN vcs import src < src/Multi-Robot-Graph-SLAM/mrg_slam.repos

RUN . /opt/ros/jazzy/setup.sh && \
    colcon build --parallel-workers 1 || echo "Build failed, user can fix later"

ENTRYPOINT ["/entrypoint.sh"]

# Add source to bashrc for interactive shells
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "if [ -f /root/ros2_ws/install/setup.bash ]; then source /root/ros2_ws/install/setup.bash; fi" >> /root/.bashrc

