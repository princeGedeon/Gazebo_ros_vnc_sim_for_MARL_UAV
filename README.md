# Multi-UAV Swarm Coverage & Mapping Framework 🚁🌍

**Research Project: Decentralized Multi-Agent Reinforcement Learning (MARL) for Cooperative 3D Urban Mapping.**

## 1. Project Overview

This framework implements a **Decentralized Partially Observable Markov Decision Process (Dec-POMDP)** to solve the cooperative coverage path planning (CPP) problem in unknown 3D urban environments.

It features a **Hybrid Architecture** combining:
*   **Distributed Graph SLAM** (`mrg_slam`) using **360° Lidar** for localization (The "Skeleton").
*   **Volumetric Mapping** (`VoxelManager`) using **Downward-Facing Lidar** for ground/obstacle coverage (The "Flesh").
*   **Multi-Agent RL (MAPPO)** for autonomous decision-making using `SKRL` and `PettingZoo`.

## 2. Key Features

*   **Dual-Sensor Setup**:
    *   **Lidar 360°**: Used for SLAM, Loop Closures, and Obstacle Avoidance (Horizontal).
    *   **Lidar Down (Nadir)**: Dedicated sensor for mapping the urban surface and roofs (Vertical).
*   **Procedural City Generation**: Generate sparse to dense urban canyons with a single command.
*   **Data Mule Logic**: UAVs must physically return to base stations to offload data, simulated by a realistic buffer constraints.
*   **Sparse Voxel Hashing**: Optimized memory management for large-scale 3D mapping.
*   **Global Georeferencing**: Fusion of GPS anchors with SLAM graph for GIS-compatible output (`.npy`, `.las`).

## 3. Installation & Build

```bash
cd ~/ros2_ws
colcon build --symlink-install --packages-select swarm_sim
source install/setup.bash
```

## 4. Usage Guide

### A. Procedural City Generation 🏙️
Generate a custom testing ground:

```bash
# Generate a dense 100x100m city with 8m tall buildings
python3 src/swarm_sim_pkg/swarm_sim/assets/worlds/generate_city.py \
    --output src/swarm_sim_pkg/swarm_sim/assets/worlds/generated_city.sdf \
    --mode full \
    --width 100 \
    --length 100 \
    --max_height 8
```

### B. Launching Simulation 🚀
Launch the environment with your generated map:

```bash
ros2 launch swarm_sim super_simulation.launch.py map_file:=generated_city.sdf num_drones:=3
```

### D. Launching Multi-Robot SLAM (Optional but Recommended) 🛰️
To enable Graph SLAM and loop closures, run the SLAM nodes **in the SLAM container** (e.g., `rosette_slam`):

```bash
# Inside the SLAM container
bash src/scripts/slam_launch.sh
```
*   This launches `mrg_slam` for `uav_0`, `uav_1`, and `uav_2`.
*   Ensure the simulation is running first.

### E. Training / Debugging RL Agent 🧠
Run the PettingZoo environment loop (with SKRL integration):

```bash
# In the main ROS 2 container
python3 src/scripts/debug_rl_env.py
```
*   **Logs**: storage status (`Sto: 80%`), rewards breakdown, and battery levels.
*   **Output**: 
    *   **Occupancy Map (.npy / .laz)**: `src/swarm_sim_pkg/swarm_sim/outputs/debug_map.laz`. Use CloudCompare or similar to view the `.laz` file.
    *   **SLAM Maps (.pcd)**: `src/swarm_sim_pkg/swarm_sim/outputs/slam_map_uav_X.pcd` (if SLAM is running).

### F. Visualization in RViz 📺
You can visualize the Global Occupancy Map in real-time or post-simulation.

**1. Real-Time (During Simulation)**:
*   Open RViz2: `rviz2`
*   Set **Fixed Frame** to `world`.
*   Add a **PointCloud2** display.
*   Set **Topic** to `/coverage_map_voxels`.
*   Select **Style** as `Boxes` or `Points` to see the voxels.
*   *Note: The map updates periodically (every 10 steps in debug script).*

**2. Post-Processing (Matplotlib)**:
To see the saved `.npy` map:
```bash
python3 src/scripts/visualize_occupancy.py src/swarm_sim_pkg/swarm_sim/outputs/debug_map.npy
```

---
**Author**: [Prince Gédéon]

