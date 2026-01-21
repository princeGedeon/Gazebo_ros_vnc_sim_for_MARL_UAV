
# Implementation Plan - Scalable MARL UAV Coverage Framework

This plan outlines the restructuring of the repository to support robust research into Single and Multi-UAV Coverage Path Planning (CPP) with constraints.

## User Objectives
- **Scalable Architecture**: Separate single/multi-agent logic, easy to extend.
- **Coverage Path Planning**: Implement volumetric coverage tracking and rewards.
- **Constraints**: Support for safety constraints (collision, geofence) suitable for Constrained MARL research (MAPPO-Lagrangian).
- **Rich Environment**: 3D City/Urban structures in Gazebo.

## 1. Directory Structure Refactor (Completed)
The code is now organized as a ROS 2 Python package `swarm_sim`.

```text
src/swarm_sim_pkg/
├── setup.py            # Package config
├── package.xml         # ROS 2 dependency config
└── swarm_sim/          # Python Module
    ├── envs/
    │   ├── core/               # Shared dynamics & ROS bridges
    │   ├── single_agent/       # Gymnasium Environments (CoverageEnv)
    │   └── multi_agent/        # PettingZoo Environments (SwarmCoverageEnv)
    ├── common/                 # Utilities
    │   ├── voxel_manager.py    # 3D Volumetric Coverage Logic
    │   └── rewards.py          # Modular Reward & Constraint Engine
    ├── assets/
    │   ├── models/             # UAV SDFs
    │   └── worlds/             # City.sdf
    └── training/
        ├── train_single.py     # SB3 PPO script (Baseline)
        └── train_swarm.py      # SB3/MAPPO script (via SuperSuit)
```

## 2. Core Components

### A. The "City" World (Implemented)
- `city.sdf`: Includes buildings, obstacles, and a ground plane.

### B. Voxel Manager (Implemented)
- `voxel_manager.py`: Discretizes the world into 3D voxels.
- Tracks `visited` status (0 or 1).
- Provides local 3D observations.

### C. Constraint & Reward Module (Implemented)
- `rewards.py`:
  - Returns raw constraints dictionary (collision boolean, boundary violation).
  - Designed to feed into Constrained RL algorithms (e.g., as cost signal).
  - *Future Work*: Integrate MAPPO-Lagrangian (e.g., using `safe-rl-lib` or custom Lagrangian multiplier).

## 3. Training Workflows

We use standard PPO for now (Parameter Sharing for Swarm).
To execute:
```bash
# 1. Build
cd ~/ros2_ws
colcon build --packages-select swarm_sim --symlink-install
source install/setup.bash

# 2. Run Training
ros2 run swarm_sim train_single
# or
ros2 run swarm_sim train_swarm
```


## 4. New Features (Implemented)

### A. Modular Multi-Agent Launch
- **`multi_ops.launch.py`**:
  - Spawns `N` UAVs dynamically with namespaced topics (`/uav_i/...`).
  - Launches `god` nodes: TF Bridge for global localization.
  - Spawns **Ground Station** assets (`ground_station.sdf`).

### B. Dual-Sensor System
- **UAV Model Upgrade**:
  - `lidar_3d` (Topic: `/uav_i/sensors/lidar`): 16-channel 3D Lidar for mapping/SLAM.
  - `lidar_2d` (Topic: `/uav_i/scan`): Single-line Lidar for lightweight RL/Navigation (backward compatible).

### C. Mapping & SLAM
- **`mapping.launch.py`**:
  - Launches `octomap_server` for each drone.
  - Generates 3D Occupancy Map (Voxels) and 2D Projected Map (OccupancyGrid).
  - Uses exact transforms from Gazebo (Perfect SLAM).

## 5. Usage

### 1. Launch Simulation
```bash
# Terminal 1: Sim & Bridge
ros2 launch swarm_sim multi_ops.launch.py num_drones:=3
```

### 2. Launch Mapping (Optional)
```bash
# Terminal 2: Octomap
ros2 launch swarm_sim mapping.launch.py
```

### 3. Run Training/Control
```bash
# Terminal 3: RL Agent
ros2 run swarm_sim train_swarm
```
