
# 🏗️ Swarm Simulation Package
> **Realised by Prince Gedeon**

This repository contains a modular **Multi-Agent Reinforcement Learning (MARL)** framework for UAV swarm coverage tasks in 3D urban environments, built on **ROS 2 Jazzy** and **Gazebo Harmonic**.

## 📂 Architecture

The codebase is structured as a standard ROS 2 python package:

```text
swarm_sim_pkg/
├── setup.py                    # Build configuration (Fixed to ignore .git)
├── package.xml                 # Dependencies
└── swarm_sim/                  # Core Python Module
    ├── assets/                 # Simulation Assets
    │   ├── models/             # UAV SDF Models (x500_sensors.sdf.xacro)
    │   └── PX4-gazebo-models/  # Official PX4 Assets (Cloned)
```

## 🚀 Getting Started

**[📖 READ THE MASTER GUIDE HERE (docs/GUIDE.md)](docs/GUIDE.md)**

### 0. Prerequisites (Critical)
Before anything, you must download the official PX4 3D models.
Run this inside `src/swarm_sim_pkg/swarm_sim/assets/`:
```bash
cd src/swarm_sim_pkg/swarm_sim/assets/
git clone https://github.com/PX4/PX4-gazebo-models.git
```
*Without this, the drones will be invisible.*

### 1. Automated Launch (Recommended)
We have created a "magic script" that handles cleaning, building, and launching:
```bash
./autolaunch.sh
```
**What this script does:**
1.  **Fixes Git Permissions**: Resolves "dubious ownership" errors.
2.  **Cleans Build**: Removes conflicting artifacts.
3.  **Builds Workspace**: Compiles `swarm_sim` (ignoring large `.git` folders).
4.  **Launches**: Starts 3 drones with SLAM enabled.

### 2. Manual Launch
If you prefer manual control:
```bash
# General Launch
ros2 launch swarm_sim super_simulation.launch.py num_drones:=3

# With SLAM
ros2 launch swarm_sim super_simulation.launch.py num_drones:=3 slam:=true
```

## 🛠 Features

- **Real Visuals**: Official PX4 X500 mesh integration with spinning Lidar and visible laser rays.
- **Swarm-SLAM**: Integrated C-SLAM for collaborative mapping.
- **Volumetric Coverage**: `VoxelManager` for 3D RL tasks.
- **City Generation**: Procedural generation scripts.

### 🏙️ City Generation
You can generate custom 3D cities with random buildings:
```bash
# Inside the container:
cd src/swarm_sim_pkg/swarm_sim/assets/worlds/
python3 generate_city.py --output my_city.sdf --num_blocks 50 --mode full --seed 42
```
**Parameters:**
- `--num_blocks`: Base number of buildings.
- `--mode`: Density (`low`, `medium`, `full`).
- `--seed`: For reproducible cities.
- `--outputs`: Output filename (use this in launch: `map_file:=my_city.sdf`).

### 🔍 Visualization (RViz2)
- **Topic Reliability**: Set to **Best Effort** for Lidar/Camera.
- **Frames**: `map` or `world`.
- **Displays**: RobotModel, LaserScan/PointCloud2, Image.

## 🐛 Bug Correction History (Recent Fixes)
1.  **Visuals Recovered**: Replaced broken `drone.stl` with official `PX4-gazebo-models`.
2.  **Build Fixed**: Modified `setup.py` to exclude `.git` folders from asset globbing, preventing build failures.
3.  **SDF Syntax Error**: Fixed `inertia` tag usage (SDF vs URDF attributes) which caused models to vanish.
4.  **Autolaunch Fix**: Corrected package name `swarm_sim_pkg` -> `swarm_sim` in build command.
5.  **Dubious Ownership**: Added `git config safe.directory '*'`.
6.  **SLAM Dependencies**: Moved `numba`/`sklearn` to pip installation.

## 🤝 Credits & Inspirations
- **Swarm-SLAM (C-SLAM)**: [Lajoie et al.](https://github.com/MISTLab/Swarm-SLAM)
- **PX4 Autopilot**: Official Gazebo Models.
