# Materials & Methods (Thesis Section 3)

This document provides the technical backbone for the "Methodology" section of your thesis, focusing on the engineering challenges and solutions deployed.

## 1. Experimental Setup

### Hardware Infrastructure
*   **Compute Node**: Workstation equipped with NVIDIA GPU (RTX 30 Series recommended) + Multi-core CPU (Ryzen 9/Threadripper).
*   **Observation**: RL simulation is CPU-bound (physics stepping), while Policy Inference/Training is GPU-bound. This bottleneck dictates the training speed.

### Software Stack
*   **Simulation**: Gazebo Harmonic (Garden). Chosen for its ability to simulate aerodynamic effects and sensor noise accurately.
*   **Orchestrator**: ROS 2 Jazzy (DDS middleware). Handles inter-agent communication ($\approx$ 100Hz bandwidth).
*   **Algorithm**: Multi-Agent PPO (MAPPO) implemented in Ray RLLib.

## 2. Methodology: Addressing Key Challenges

Developing a safe multi-agent system presents three primary challenges. Here is how we solved them:

### Challenge 1: The Curse of Dimensionality (State Space Explosion)
*   **Problem**: As the number of agents $N$ increases, the joint state space $S$ grows exponentially. A centralized critic taking all states $V(s_1, ..., s_N)$ becomes untrainable.
*   **Solution**: **Decentralized Execution & Action Space Reduction (2.5D)**.
    *   **Graph-based Observation**: Each agent only observes its $k=3$ closest neighbors (Constant input size).
    *   **Fixed-Altitude Training**: We initially constrain the agents to a fixed height ($v_z=0$), effectively reducing the problem to 2.5D. This removes an entire axis of exploration, significantly speeding up early-stage convergence.

### Challenge 2: Sim-to-Real Gap (Perception)
*   **Problem**: A policy trained on perfect ground-truth positions fails in reality due to sensor noise and drift.
*   **Solution**: **2.5D Elevation Mapping & Domain Randomization**.
    *   Instead of raw 3D point clouds, we project LIDAR data into a 2.5D height map. This abstraction is robust to minor pitch/roll noise.
    *   We add Gaussian noise to the simulated Odometry during training to force the policy to be robust against localization errors.

### Challenge 3: Guaranteeing Safety
*   **Problem**: RL explores by trial-and-error, which implies crashing. In deployment, crashing is unacceptable.
*   **Solution**: **Tiered Safety Architecture**.
    *   *Tier 1 (Soft)*: Negative Reward for collisions (Learning phase).
    *   *Tier 2 (Constraints)*: Lagrangian Relaxation to satisfy collision probability constraints $\Pr(Collision) \le \delta$.
    *   *Tier 3 (Hard)*: Control Barrier Functions (CBF) acting as a final "Safety Filter" that overrides the RL action if it violates the safe set boundary $\dot{h}(x) \geq -\gamma h(x)$.

## 3. Validation Metrics

We evaluate the system performance using the following KPIs:

1.  **Safety Rate**: $\frac{\text{Episodes without Collision}}{\text{Total Episodes}}$. Target $> 95\%$.
2.  **Sparsity of Violations**: For the Lagrangian method, we measure the magnitude of constraint violation $\sum \max(0, C_k - d_k)$.
3.  **Map Entropy (SLAM)**: Measures the information gain of the constructed map over time. Lower entropy = Higher certainty.

## 5. Defense Strategy: "What if it doesn't fly perfectly?"

**Crucial Point for the Jury**: Building the *Training Infrastructure* (The Gym) is a harder engineering challenge than the flying itself.

If the drones are not yet perfectly intelligent during the demo, frame your defense around these pillars:

### A. The "Research Platform" Achievement
You did not just build a robot; you built a **Scalable Multi-Agent Research Bench**.
*   **Show the Stack**: Display the `architecture.md` diagram. Highlight the integration of Docker + ROS 2 + Gazebo + Ray RLLib. This is "Senior Engineer" level integration.
*   **Show the Math**: Walk through the `math_model_convergence.md`. Prove you understand *how* they learn, even if they need 100M more steps to master it.

### B. The "Scientific Validity" Argument
"The experiment is running correctly; the training curve is just starting."
*   **Show Tensorboard**: If the `entropy` is decreasing or `reward` is slowly rising, that is scientific proof of learning.
*   **Explain the Timeline**: Use the data from `training_guide.md` ("Why 1 Month is not enough"). Explain that you prioritized **System Stability** and **Mathematical Rigour** (Lagrangian/CBF) over a "hacky" demo.

### C. The "Live Demo"
*   **Do not rely on a converged policy**.
*   **Show the "Loop"**: Launch the simulation. Show that:
    1.  Sensors works (LiDAR points in Rviz).
    2.  Communication works (ROS 2 topics active).
    3.  Training is stepping (Terminal logs scrolling).
*   *Conclusion*: "The machine is built and running. The intelligence is currently being distilled."
