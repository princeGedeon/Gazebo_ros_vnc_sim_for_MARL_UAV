# Training Guide & Environment Reference

This document details the training pipeline, action/state definitions, and the practical realities of training large-scale MARL systems (and why it takes so long).

## 1. Launching Training

Training scripts are located in `scripts/`. They orchestrate the Docker environment and Ray RLLib clusters.

### Key Commandments
To start training, run one of the following from the root or inside the `sim` container:

*   **Case 1: Simple Navigation (Baseline)**
    ```bash
    ./scripts/train_case_1_simple.sh
    ```
    *Goal*: Point-to-point navigation. No complex constraints.

*   **Case 2: Lagrangian Relaxation (Soft Constraints)**
    ```bash
    ./scripts/train_case_2_lagrange.sh
    ```
    *Goal*: Learn safety boundaries via adaptive penalty multipliers. Harder to converge.

*   **Case 3: Control Barrier Functions (CBF)**
    ```bash
    ./scripts/train_case_3_cbf.sh
    ```
    *Goal*: Guarantee safety by filtering actions. Requires solving a QP (Quadratic Program) at every step.

## 2. Action Space (Simplified to 2.5D)

To accelerate convergence, we simplify the control problem by **fixing the flight altitude ($z$)**.
**Strategy**: The agents first perform an automatic takeoff to a safe altitude ($h_{safe}$) where sensors clearly see the ground and obstacles. Once stabilized, the training episode begins, and the **vertical control is locked** ($v_z \approx 0$).

**Action**: `Box(-1.0, 1.0, shape=(3,))` (Fixed Altitude Phase)

| Index | Component | Description | Range |
| :--- | :--- | :--- | :--- |
| 0 | $v_x$ | Forward/Back | $\pm 1.0$ m/s |
| 1 | $v_y$ | Left/Right | $\pm 1.0$ m/s |
| 2 | $\omega_z$ | Yaw Rate | $\pm 1.0$ rad/s |

*> Note: The vertical axis is managed by a low-level PID controller maintaining $z = h_{safe}$ during the learning phase.*

## 3. Observation Space

Local observations only (Partially Observable).

*   **LIDAR (2.5D)**: 1x360 vector representing the minimum distance or max height in sectors. Reduced from 3D for efficiency.
*   **Proprioception**: Own state (position, velocity, orientation).
*   **Relative Goals**: Polar coordinates to the next waypoint.
*   **Neighbors**: Relative positions of $k$ nearest neighbors (for flocking/separation).

## 4. The Engineering Challenge: Why "1 Month" isn't enough

A common misconception is that RL agents learn overnight. For a complex Multi-Agent UAV task with safety guarantees, **training is extremely time-intensive**. Here is the breakdown:

### A. The Sample Efficiency Bottleneck
*   **Concept**: RL is "sample inefficient". It needs millions of interactions to learn what *not* to do.
*   **Reality**: MAPPO (Multi-Agent PPO) usually requires ~10-50 Million timesteps to converge on complex tasks.
*   **Throughput**: Even with parallel environments, Gazebo is a heavy simulator.
    *   *Real-Time Factor (RTF)*: With 10 drones + Lidar, RTF often drops to 0.5x (slower than real time).
    *   *Daily yield*: You might only collect 1M steps per day on a single GPU workstation.
    *   *Math*: 50M steps / 1M per day = **50 Days** just for ONE good run.

### B. The "Curriculum Learning" Necessity
You cannot throw agents into a dense forest immediately. They will crash instanly and learn nothing (sparse reward problem).
1.  **Stage 1 (Empty World)**: Learn to fly to target. (~1 week)
2.  **Stage 2 (Static Obstacles)**: Learn to avoid cylinders. (~1-2 weeks)
3.  **Stage 3 (Dynamic Swarm)**: Learn to avoid each other. (~2 weeks)
*   **Total**: The sequential nature of curriculum learning multiplies the duration.

### C. Hyperparameter Tuning Hell
Lagrangian methods introduce new headers:
*   *Penalty Multiplier Learning Rate*: Too high? Agent stays still to be safe. Too low? Agent ignores safety.
*   Finding the right balance often requires running 5-10 experiments in parallel, further dividing your compute resources.

### Conclusion
"1 Month" is a tight sprint for a Proof of Concept (PoC) in MARL. For a thesis-grade, fully converged, collision-free swarm policy with math proofs, **2-3 months** on a dedicated GPU cluster is the realistic timeline.
