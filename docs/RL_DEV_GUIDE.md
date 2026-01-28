# Swarm Coverage RL Environment Guide

## 1. Environment Configuration (`SwarmCoverageEnv`)

You can configure the environment with the following parameters during initialization:

```python
env = SwarmCoverageEnv(
    num_drones=3,
    station_config=1,          # Number of stations OR list of [x, y]
    min_height=2.0,            # Minimum flight altitude (meters)
    max_height=10.0,           # Maximum flight altitude (meters)
    nfz_config='default'       # No-Fly Zone config
)
```

### No-Fly Zones (NFZ)
The `nfz_config` parameter controls the generation of restricted areas (Red Zones):

*   **'default'**: Generates **one** random circular zone (Radius 2-5m).
*   **Integer (e.g., 3)**: Generates **N** random circular zones.
*   **List (e.g., `[(5, 5, 3.0), (-5, -5, 2.0)]`)**: Manually specifies zones as `(x, y, radius)`.

**Visualization:** These zones appear as **Red Semi-Transparent Cylinders** in RViz.

---

## 2. Reward System Updates

### A. Altitude Constraints
*   **Goal:** Keep drones between `min_height` and `max_height`.
*   **Penalty:** 
    *   If `z < min_height`: Linear penalty `-(min - z) * 2.0`.
    *   If `z > max_height`: Linear penalty `-(z - max) * 2.0`.
*   **Exception (Landing):** If the drone is within **2.5m** of a Ground Station, it is **allowed** to descend below `min_height` (for recharge/offloading) without penalty.

### B. No-Fly Zones (NFZ)
*   **Goal:** Avoid entering Red Zones.
*   **Penalty:** If the drone enters a zone (distance < radius + 0.5m), it receives a **severe penalty** of **-10.0 per step**.

### C. Coverage & Exploration
*   **Rewards:** Distributed to the team based on **Global Map Progress**.
*   **Logic:** As drones explore, they update their local maps. When they return to base to offload, the "Central Map" is updated.

---

## 3. Visualization
*   **Green Spheres:** Ground Stations (Recharge/Offload zones).
*   **Red / Blue Ellipses:** Communication Range.
*   **Red Cylinders:** No-Fly Zones (Avoid!).
