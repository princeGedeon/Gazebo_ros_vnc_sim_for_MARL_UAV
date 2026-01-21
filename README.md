
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

**[📖 READ THE MASTER GUIDE HERE (docs/GUIDE.md)](docs/GUIDE.md)**

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
# This launch file starts Gazebo with the generated city and spawns UAVs
ros2 launch swarm_sim simulation.launch.py
```
*Tip: Open a VNC session (http://localhost:6080) to see the GUI.*

### 3. Run Training
In a new terminal (ensure you source `install/setup.bash`):

**Single Agent:**
```bash
ros2 run swarm_sim train_single
```

**Multi-Agent Swarm:**
ros2 run swarm_sim train_swarm
```

## 🛠 Features

### 1. Flexible Simulation & External Maps
Launch using diverse map sources (worlds or individual models):
```bash
# Default City World
ros2 launch swarm_sim multi_ops.launch.py

# External Map Model (e.g. from engcang/gazebo_maps)
# Launches empty world + spawns model at (0,0,0)
ros2 launch swarm_sim multi_ops.launch.py map_type:=model map_file:=/abs/path/to/model.sdf
```

### 2. GIS & Mapping
- **Decentralized Octomap**: `ros2 launch swarm_sim mapping.launch.py`
- **Save to File**:
  ```bash
  python3 src/swarm_sim_pkg/swarm_sim/common/save_map.py my_city_map.bt
  ```
  Generates `my_city_map.bt` (Octomap) and `my_city_map.bt.json` (GPS Metadata).

### 3. Advanced Swarm Logic (RL)
- **Global Coverage Reward**: Team based reward for uncovering new voxels.
- **Battery System**: 
  - Real-time drain based on velocity.
  - **Return-To-Base**: Strong penalties for critical battery away from station.
  - **Recharge**: Hover near Ground Station (Red Cylinder at 5,5).
- **Decentralized Loop Closure**: Agents share map data only when within interaction range (<3m).

### 4. Real Swarm-SLAM (Advanced)
To replace the simulated logic with **Real C-SLAM** (MISTLab/Swarm-SLAM):

1.  **Install Dependencies** (Requires Sudo/Root):
    ```bash
    bash setup_real_slam.sh
    source install/setup.bash
    ```
2.  **Launch Simulation**:
    ```bash
    ros2 launch swarm_sim multi_ops.launch.py
    ```
3.  **Launch SLAM Backend**:
    ```bash
    ros2 launch swarm_sim swarm_slam.launch.py num_drones:=3
    ```
    This runs `cslam_lidar` nodes for each drone, performing real decentralized loop closure detection.



- **Volumetric Coverage**: Uses `VoxelManager` to track 3D coverage of a city environment.
- **Constraints**: Includes a generic `RewardEngine` capable of checking collision and boundary constraints, ready for Constrained MARL (e.g. Lagrangian approaches).
- **Procedural Cities**: Includes a script to generate random urban layouts.
- **Visualization**: Publishes `MarkerArray` to `/coverage_map` for real-time coverage visualization in RViz.

## 🔮 Roadmap / Future Work

- **MAPPO-Lagrangian**: Modify `train_swarm.py` to use a constrained optimization algorithm using the `info['constraints']` values.
- **Decentralized SLAM**: Integrate specific ROS 2 SLAM packages (like `slam_toolbox` or `rtabmap`) for mapping, feeding the map into the policy instead of ground truth voxels.
