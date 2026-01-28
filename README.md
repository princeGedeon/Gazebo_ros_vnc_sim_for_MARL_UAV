# Multi-UAV Swarm Coverage & Mapping Framework 🚁🌍

**Research Project: Decentralized Multi-Agent Reinforcement Learning (MARL) for Cooperative 3D Urban Mapping.**

## 📚 Documentation Dashboard

Key technical documents for the project architecture and training formulation:

| Document | Description |
| :--- | :--- |
| **[DEC-POMDP Formulation](docs/DEC_POMDP.md)** | Formal mathematical definition of the problem ($S, A, \Omega, R, C$). |
| **[System Architecture](docs/SYSTEM_ARCHITECTURE.md)** | Mermaid graph of the ROS 2 Nodes, Topics, and Data Flow. |
| **[Scripts Guide](scripts/README.md)** | Explanation of utility scripts (`launch_all.sh`, `test_map_export.py`, etc.). |
| **[RL Dev Guide](docs/RL_DEV_GUIDE.md)** | (Existing) Developer guide for RL environment and debugging. |

---

## 1. Project Overview

This framework implements a **Decentralized Partially Observable Markov Decision Process (Dec-POMDP)** to solve the cooperative coverage path planning (CPP) problem in unknown 3D urban environments.

It features a **Hybrid Architecture** combining:
*   **Distributed Graph SLAM** (`mrg_slam`) using **360° Lidar** for localization (The "Skeleton").
*   **Volumetric Mapping** (`VoxelManager`) using **Downward-Facing Lidar** for ground/obstacle coverage (The "Flesh").
*   **Multi-Agent RL (MAPPO)** for autonomous decision-making using `SKRL` / `RLLib` and `PettingZoo`.

## 2. Key Features

*   **Dual-Sensor Setup**:
    *   **Lidar 360°**: Obstacle Avoidance & SLAM.
    *   **Lidar Down**: Mapping urban surface/roofs.
*   **Procedural City Generation**: Random urban canyons.
*   **Constraint-Aware RL**: Penalty-based shaping for Battery, NFZ, and Altitude.
*   **Global Georeferencing**: Outputs **UTM-georeferenced** `.laz` point clouds compatible with CloudCompare.

## 3. Installation

```bash
cd ~/ros2_ws
colcon build --symlink-install --packages-select swarm_sim
source install/setup.bash
```

## 4. Quick Start 🚀

### A. Launch Simulation + Training
We provide a unified launch script in the `scripts/` folder:

```bash
# Launch Simulation (Gazebo) AND Training Agent (MAPPO)
./scripts/launch_all.sh train
```
*This starts Gazebo in the background and attaches the RL trainer.*

### B. Generate Custom City
```bash
python3 src/swarm_sim_pkg/swarm_sim/assets/worlds/generate_city.py \
    --output src/swarm_sim_pkg/swarm_sim/assets/worlds/generated_city.sdf \
    --mode full --width 100 --length 100 --max_height 8
```

## 5. Map Export & Visualization 🗺️

### Real-Time Visualization (RViz)
*   **Topic**: `/coverage_map_voxels` (PointCloud2)
*   The map updates as drones explore.

### Exporting to CloudCompare
The system automatically exports the map as a georeferenced `.laz` file (e.g., `test_map_output.laz` or via `env.save_occupancy_map()`).
1.  Open **CloudCompare**.
2.  Drag & drop the `.laz` file.
3.  Accept the "Global Shift" (UTM Coordinates).

## 6. Project Structure

*   `docs/` - System documentation.
*   `scripts/` - Utility scripts for launching, testing, and installing.
*   `src/` - Source code for ROS 2 packages (`swarm_sim_pkg`).
*   `outputs/` - Generated maps and debug logs.

---
**Author**: Prince Gédéon
