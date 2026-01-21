
# 🏗️ Swarm Simulation Package
> **Realised by Prince Gedeon**

This repository contains a modular **Multi-Agent Reinforcement Learning (MARL)** framework for UAV swarm coverage tasks in 3D urban environments, built on **ROS 2 Jazzy** and **Gazebo Harmonic**.

## 📂 Architecture

The codebase is structured as a standard ROS 2 python package:

```text
swarm_sim_pkg/
├── setup.py                    # Build configuration
├── package.xml                 # Dependencies
└── swarm_sim/                  # Core Python Module
    ├── envs/                   # RL Environments
    │   ├── core/               # Shared Logic (UAV ROS Interface)
    │   ├── single_agent/       # Gymnasium Envs (Baseline)
    │   └── multi_agent/        # PettingZoo Envs (Swarm Logic)
    ├── common/                 # Utilities
    │   ├── voxel_manager.py    # 3D Volumetric Coverage Tracking
    │   ├── rewards.py          # Modular Reward & Constraint Engine
    │   └── viz_utils.py        # RViz Visualization Helpers
    ├── assets/                 # Simulation Assets
    │   ├── models/             # UAV SDF Models
    │   └── worlds/             # Procedural City SDF
    └── training/               # Training Scripts
        ├── train_single.py     # Single Agent PPO
        └── train_swarm.py      # Multi-Agent MAPPO (Param Sharing)
```

## 🚀 Getting Started

### 1. Build the Package
Inside the dev container:
```bash
# Fix for git safety errors in container
git config --global --add safe.directory '*'

cd /root/ros2_ws
colcon build --packages-select swarm_sim_pkg --symlink-install
source install/setup.bash
```

### 2. 🚀 Quick Start (Automated)
Run the auto-launcher to clean, build, and launch everything in one go:
```bash
./autolaunch.sh
```

### 3. Manual Launch
If you prefer manual control:
```bash
ros2 launch swarm_sim super_simulation.launch.py num_drones:=3
```

**Launch 3 Drones with SLAM (Collaborative Mapping):**
```bash
ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 slam:=true
```

**Launch 1 Single Drone:**
```bash
ros2 launch swarm_sim super_simulation.launch.py num_drones:=1
```

**Launch 2 Drones:**
```bash
ros2 launch swarm_sim super_simulation.launch.py num_drones:=2
```

### 3. 👁️ Visualization (RViz2)
RViz2 opens automatically. **If topics show "No messages received", CHECK QOS:**
1.  **Global Options > Fixed Frame**: Set to `map` or `world`.
2.  **Add > RobotModel**: Set Topic to `/uav_0/robot_description`.
    -   *Issue?* Ensure "Description Source" is Topic.
3.  **Add > PointCloud2**: Set Topic to `/uav_0/sensors/lidar`.
    -   **CRITICAL**: Under "Topic" settings in RViz, change **Reliability Policy** to **Best Effort**.
    -   *Style*: Change "Points" size to 3 to see them better.
4.  **Add > Image**: Set Topic to `/uav_0/camera/image_raw` (Front) or `/uav_0/down_camera/image_raw` (Down).
    -   **CRITICAL**: Change **Reliability Policy** to **Best Effort**.
5.  **Add > TF**: Enabled show "Frames" to see the drone moving.

### 4. 🔍 Inspect Data (RQT)
If you want to debug raw data or check connections:
```bash
rqt
```
-   **See all Topics**: Plugins -> Topics -> **Topic Monitor**. (Check boxes to see data rate).
-   **See Images**: Plugins -> Visualization -> **Image View**. (Select `/uav_0/down_camera/image_raw`).
-   **Graph**: Plugins -> Introspection -> **Node Graph**.

### 🛠️ Advanced / Specific Launch
If you need granular control (e.g. without RViz or specific maps):
```bash
# Just the simulation (No RViz)
ros2 launch swarm_sim multi_ops.launch.py num_drones:=3

# Using Helper Script for specific maps
./src/launch_session.sh Acourse 3
```

### 3. Run Training
In a new terminal (ensure you source `install/setup.bash`):

**Single Agent:**
```bash
ros2 run swarm_sim train_single
```

**Multi-Agent Swarm:**
```bash
ros2 run swarm_sim train_swarm
```

## 🛠 Features

- **Volumetric Coverage**: Uses `VoxelManager` to track 3D coverage of a city environment.
- **Constraints**: Includes a generic `RewardEngine` capable of checking collision and boundary constraints, ready for Constrained MARL (e.g. Lagrangian approaches).
- **Procedural Cities**: Includes a script to generate random urban layouts.
- **Visualization**: Publishes `MarkerArray` to `/coverage_map` for real-time coverage visualization in RViz.
- **Sensors**: 
  - **Lidar**: 360° Spinning Lidar (`/{name}/sensors/lidar`)
  - **Sonar**: Downward facing range sensor (`/{name}/sensors/sonar`)
  - **Camera**: Forward-facing (`/{name}/camera/image_raw`)
  - **Down Camera**: Downward-facing (`/{name}/down_camera/image_raw`)
- **City Generation**: Procedural city generator with density modes (`full`, `medium`, `low`) and seeding.

## 🏙️ City Generation
Generate custom maps:
```bash
python3 src/swarm_sim_pkg/swarm_sim/assets/worlds/generate_city.py \\
    --mode full --seed 123 --width 200 --length 200
```
*Supports `WindEffects` plugin by default.*

## 🔮 Roadmap / Future Work

- **MAPPO-Lagrangian**: Modify `train_swarm.py` to use a constrained optimization algorithm using the `info['constraints']` values.
- **Decentralized SLAM**: Integrate specific ROS 2 SLAM packages (like `slam_toolbox` or `rtabmap`) for mapping, feeding the map into the policy instead of ground truth voxels.

### 4. GPU vs CPU Rendering
By default, the container attempts to use the **GPU** (`RENDERING_MODE=gpu`).
- **GPU Mode**: Uses NVIDIA drivers for OpenGL/Vulkan. Required for fast Gazebo performance.
- **CPU Mode**: Falls back to software rendering (llvmpipe). Useful for debugging if no GPU is available.

To force CPU mode:
```bash
export RENDERING_MODE=cpu
docker compose up -d
```
*Note: `glxinfo` inside Xvfb might still show `llvmpipe` for the display, but Gazebo's internal sensor rendering (Vulkan) will use the GPU.*

### 5. Using a Real VNC Client (Faster)
The web interface (NoVNC) can be slow. For better performance:
1. Download a VNC Viewer (e.g., [RealVNC](https://www.realvnc.com/en/connect/download/viewer/) or [Remmina](https://remmina.org/)).
2. Connect to: `localhost:5901`
3. If asked for a password, it is currently empty (or check entrypoint).

This direct connection is often smoother than the browser-based one.
