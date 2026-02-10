# System Architecture

This document outlines the high-level architecture of the Multi-Agent Reinforcement Learning (MARL) simulation for UAV navigation and SLAM.

## 1. System Overview

The system is designed to train and evaluate swarms of UAVs capable of autonomous navigation, obstacle avoidance, and collaborative mapping in complex environments.

### Core Stack
*   **ROS 2 Jazzy**: The underlying communication backbone (DDS) for real-time sensor data exchange.
*   **Gazebo (Garden/Harmonic)**: High-fidelity physics engine simulating UAV dynamics, IMU, and LiDAR sensors.
*   **Ray RLLib**: Distributed reinforcement learning framework handling the PPO-based training pipeline.
*   **PyTorch**: The deep learning backend for policy networks.
*   **Docker**: Containerized environment ensuring reproducibility across GPU nodes.

## 2. Containerized Microservices

The architecture is split into two primary containers to decouple simulation/training physics from the heavy computational load of SLAM.

### `sim` (Simulation & Training)
*   **Base**: `ros2-jazzy-swarm-sim`
*   **Role**: Hosting the Gazebo physics world and the RL Agent loop.
*   **Key Design**:
    *   **Unified Process**: Gazebo and the RL script run in the same container to minimize latency for step-by-step physics stepping.
    *   **Headless by Default**: Rendering is offloaded to VNC only when debugging `xvfb` to save GPU cycles for tensor operations.

### `slam` (Localization & Mapping)
*   **Base**: `aserbremen/mrg_slam_jazzy`
*   **Role**: Consumes sensor data to build a global map.
*   **Optimization**: Runs efficiently on CPU/GPU depending on the backend, ensuring map building doesn't slow down the RL training steps (which are synchronized).

## 3. Design Decision: 3D vs 2.5D Mapping

One of the critical engineering challenges was the dimensionality of the mapping representation for the RL observation space.

### The Challenge: "Why not full 3D Voxels?"
Initially, we considered feeding full 3D Voxel Grids (Octomap) to the policy network (CNN).
*   **Bottleneck**: A 3D CNN on a $64^3$ voxel grid is computationally Prohibitive for *every single step* of an RL agent, especially with $N$ agents. It drastically reduces the **Sample Efficiency** and Training FPS.
*   **Sparsity**: Most 3D airspaces are empty. Processing thousands of empty voxels is wasted compute.

### The Solution: 2.5D Elevation Mapping
We adopted a **2.5D Elevation Map** (or Height Map) approach.
*   **Mechanism**: We project the 3D LiDAR point cloud onto a 2D grid where each pixel value represents the *maximum height* of the obstacle in that cell.
*   **Benefit**: This reduces the input from $H \times W \times D$ to $H \times W \times 1$. We can use standard 2D CNNs (like ResNet encoders) which are orders of magnitude faster and easier to train.
*   **Sufficiency**: For a UAV flying at variable altitudes, knowing the *height* of the terrain below/ahead is usually sufficient to plan a collision-free 2.5D trajectory (changing altitude to overfly obstacles).

## 4. Data Flow Architecture

1.  **Sensors (Gazebo)** $\rightarrow$ **Shared Memory** $\rightarrow$ **ROS 2 Topics**
    *   Raw LiDAR data involves massive bandwidth. We use `IPC` (Inter-Process Communication) and `network: host` to avoid Docker bridge overhead.
2.  **State Aggregation**:
    *   Each agent constructs its local observation tensor $O_t$: `[Lidar_2.5D, Own_State, Neighbor_States]`.
3.  **Policy Inference (PyTorch)**:
    *   The `Actor` network outputs actions (Velocity Commands).
    *   **Latency Constraint**: Inference must happen within the physics time-step window (e.g., < 50ms).

## 5. File Structure
```bash
/
├── Dockerfile              # Simulation image definition
├── docker-compose.yml      # Service orchestration (GPU passthrough enabled)
├── src/
│   ├── swarm_sim_pkg/      # Core RL environment wrapper
│   ├── mrg_slam/           # Graph-based SLAM implementation
│   └── ...
├── docs/                   # Documentation (You are here)
└── scripts/                # Training entry points
```
