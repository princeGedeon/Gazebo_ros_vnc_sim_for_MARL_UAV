# Formal DEC-POMDP Formulation

The Multi-UAV 3D Coverage problem is formally defined as a **Decentralized Partially Observable Markov Decision Process (DEC-POMDP)**.

**Tuple**:  `M = < I, S, A, T, R, Ω, O, γ, C >`

## 1. Agents (I)
A set of **N** homogeneous UAV agents:
`I = {1, ..., N}`

## 2. Global State (S)
The true state of the environment at time *t* (unobservable by individual agents):
`s_t = { M_t, X_t, B_t, K_t }`

*   **Map (M_t)**: Global Occupancy Grid, where each voxel `v ∈ {0, 1}` (Unknown/Known).
*   **Joint Pose (X_t)**: States of all UAVs `X_t = {x_1, ..., x_N}`.
    *   Each `x_i = [px, py, pz, vx, vy, vz, roll, pitch, yaw]`.
*   **Battery (B_t)**: Battery levels for all agents.
*   **Storage (K_t)**: Data buffer usage for all agents.

## 3. Controls / Actions (A)
Each agent *i* executes a control input `u_i` (Velocity Command):
`u_i = [vx, vy, vz, yaw_rate]`
*   **Constraint**: `u_i ∈ [-V_max, V_max]^4`
*   The system operates in **Velocity Control Mode**.

## 4. Transition (T)
*   **Dynamics**: `x_{t+1} = f(x_t, u_t)` (Quadrotor physics).
*   **Map Update**: `M_{t+1} = M_t ∪ FOV(x_{t+1})` (New voxels discovered).

## 5. Observations (Ω)
Each agent receives a partial observation `o_i`:
`o_i = < x_local, M_local, Lidar, IMU, Neighbors >`

*   **Local Map**: 7x7x5 voxel grid around the agent.
*   **Lidar**: 16-sector distance array.
*   **IMU**: Acceleration and Angular Velocity.
*   **Neighbors**: Relative position of nearby drones.

## 6. Rewards (R)
Goal: Maximize discounted return `J = Σ γ^t * R_t`.

`R_t = R_coverage + R_safety + R_energy + R_stability`

1.  **Exploration (R_cov)**: `+5.0` points per NEW voxel discovered.
2.  **Safety (R_safe)**: 
    *   `-100` if Collision (`dist < 0.3m`).
    *   `-10` if in No-Fly Zone.
3.  **Energy (R_energy)**: Penalty for distance to station if Battery is LOW.
4.  **Stability (R_stab)**: Penalty for high tilt angles (roll/pitch).

## 7. Constraints (C)
The system enforces the following constraints:

### A. Safety
*   **Collision**: Distance between drones > `d_safe` (0.5m).
*   **Geofence**: `Z_min (2m) < Altitude < Z_max (10m)`.
*   **NFZ**: Agent position must NEVER be inside a Red Zone.

### B. Physical
*   **Actuation**: Velocity commands clamped to `+/- 1.0 m/s`.
*   **Battery**: Flight terminates if `Battery <= 0%`.

### C. Data & Comms
*   **Storage**: Buffer limited to `K_max` voxels.
*   **Offloading**: Data transfer only possible if `dist(Agent, Station) < 2.0m`.
