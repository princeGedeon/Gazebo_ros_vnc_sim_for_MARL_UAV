
# 🏗️ Swarm Simulation Package

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
cd /root/ros2_ws
colcon build --packages-select swarm_sim --symlink-install
source install/setup.bash
```

### 2. Launch Simulation & Visualization
Start Gazebo, the Bridge, and RViz:
```bash
# Default: 3 Drones in City
ros2 launch swarm_sim multi_ops.launch.py num_drones:=3

# Custom Number of Drones
ros2 launch swarm_sim multi_ops.launch.py num_drones:=5

# Using the Helper Script (for specific maps)
./src/launch_session.sh city 3       # Default City
./src/launch_session.sh Acourse 2    # Competition Track
```

### Launch Arguments
- `num_drones` (default: 3): Number of UAVs to spawn.
- `map_type` (default: 'world'): 'world' (full SDF) or 'model' (empty world + model).
- `map_file`: Path or name of the world file.
*Tip: Open a VNC session (http://localhost:6080) to see the GUI.*

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
- **City Generation**: Procedural city generator with density modes and seeding.
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
