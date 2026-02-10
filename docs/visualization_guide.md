# Visualization Guide (TensorBoard)

This document explains how to visualize the training progress in real-time using TensorBoard, which is integrated with Ray RLLib.

## 1. Launching TensorBoard

Since the simulation is running in a Docker container with `network: host`, you can access the logs directly from your host machine (if you mount the volume) or by running TensorBoard inside the container.

### Option A: From inside the container (Recommended)
1.  Open a new terminal and enter the running container:
    ```bash
    docker exec -it rosette_sim bash
    ```
2.  Navigate to the workspace:
    ```bash
    cd /root/ros2_ws
    ```
3.  Launch TensorBoard pointing to the results directory:
    ```bash
    tensorboard --logdir ./rllib_results --bind_all --port 6006
    ```
4.  Open your browser on your host machine and go to:
    **http://localhost:6006**

## 2. Key Metrics to Watch

TensorBoard will display many graphs. Here are the most pertinent ones for your thesis:

### A. Performance (Validation of Intelligence)
*   **`ray/tune/episode_reward_mean`**: The most important curve. It should generally **increase** over time.
    *   *Initial Phase*: Likely low/negative (crashing).
    *   *Learning Phase*: Steep rise (finding goal).
    *   *Convergence*: Platueaus at a high value.
*   **`ray/tune/episode_len_mean`**: Steps per episode.
    *   If decreasing: Agents are reaching the goal faster.
    *   If very low constantly: Agents might be crashing immediately.

### B. Safety (Lagrangian/CBF)
*   **`ray/tune/custom_metrics/cost_rate_mean`**: The frequency of constraint violations (collisions).
    *   *Goal*: Should drop below your limit (e.g., 0.05).
*   **`ray/tune/custom_metrics/lambda_mean`**: The value of the Lagrange Multiplier.
    *   *Interpretation*: If this rises, the "Safety Policeman" is increasing the penalty for crashing.

### C. Training Stability
*   **`ray/tune/policy_entropy_mean`**: Measure of randomness in the policy.
    *   Should **decrease** over time as the agent becomes more confident.
    *   If it drops too fast to 0: Premature convergence (bad).

## 3. Real-Time Observation Data
To see *exactly* what the drone sees (LIDAR, Cameras), TensorBoard is not enough. You must use **RViz**.

1.  The container launches a VNC server on `localhost:5901`.
2.  Connect using a VNC Client (like Remmina or TigerVNC).
3.  Inside the graphical interface, `rviz2` should be running.
4.  You will see:
    *   **Red Points**: The 2.5D LiDAR scan hits.
    *   **Robot Model**: The drone's estimated attitude.
    *   **Map**: The occupancy grid being built by the SLAM module.
