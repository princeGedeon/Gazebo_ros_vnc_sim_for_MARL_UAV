# MARL Research Guide: Swarm Coverage

This guide explains how to use your Multi-UAV environment with two leading MARL libraries: **Ray RLlib** and **TorchRL BenchMARL**.

## 1. Libraries Comparison

| Feature | **Ray RLlib** (`train_mappo.py`) | **BenchMARL** (`train_benchmarl.py`) |
| :--- | :--- | :--- |
| **Best For** | Large-scale engineering, distributed training, complex distributed policies. | **Academic Research**, SOTA algorithm benchmarking, ease of use with PyTorch. |
| **Setup** | Complex config, heavy dependencies (Ray). | Clean PyTorch-style API, modular. |
| **Algorithms** | PPO, MAPPO, IMPALA, DQN, SAC... | IPPO, MAPPO, QMIX, MADDPG, MASAC... |
| **Recommendation** | Use if you need to scale to clusters or heavily customize the distributed rollout. | **Use for your Research Papers**. It's built for comparing algorithms precisely. |

---

## 2. Visualization Updates
We have updated the visualization (`viz_utils.py`) to help you debug:
*   **Workspace Boundary**: A **White Line Box** now shows the operation limits.
*   **No-Fly Zones (NFZ)**: **Red Cylinders**.
*   **Agent Colors**: Each drone's Lidar/FOV cone now has a unique color:
    *   `uav_0`: **Red**
    *   `uav_1`: **Green**
    *   `uav_2`: **Blue**
    *   (and Yellow, Cyan, Magenta for others)

---

## 3. Training & Checkpointing

### Option A: Ray RLlib (Existing)
Already set up in `train_mappo.py`.
*   **Launch**: `./start_training.sh`
*   **Checkpoints**: Saved automatically in `~/ray_results/` or `./rllib_results`.
*   **Resume**: Pass the checkpoint path to `PPOConfig().restore(path)`.

### Option B: BenchMARL (New)
For a cleaner research loop using TorchRL.

**Installation**:
```bash
pip install benchmarl torchrl
```

**Training**:
```bash
python3 src/swarm_sim_pkg/swarm_sim/training/train_benchmarl.py
```

**Checkpoints**: 
BenchMARL saves experiments in `./benchmarl_logs/`. You can load policy weights directly via PyTorch:
```python
model.load_state_dict(torch.load("checkpoint.pt"))
```

---

## 4. Constraint Configurations
To penalize agents for entering restricted zones or leaving the area:

1.  **Altitude**: Enforced via `min_height` / `max_height` args. (Exceptions made for Landing zones).
2.  **NFZ**: Configure strict penalties (`-10`) for entering Red Zones.
3.  **Boundary**: Configure soft/hard penalties if they leave the +/- 20m box (handled in code via `x_range`).

---

## 5. Visualization & Logs (How-To)

### Can I visualize *during* training?
**YES.**
Since our environment communicates with ROS 2 / Gazebo in real-time:
1.  Launch the training script (terminal 1).
2.  Open **RViz** in a separate terminal:
    ```bash
    rviz2 -d src/swarm_sim_pkg/default.rviz
    ```
3.  You will see the drones moving, the **Red NFZ Cylinders**, and the **Colored Lidar Cones** updating live as the training loop executes steps.

### Where are the logs?
*   **RLlib**: Look in `~/ray_results/` (default) or the `./rllib_results` folder created by our script. Use `tensorboard --logdir=./rllib_results` to view reward curves.
*   **BenchMARL**: Look in `./benchmarl_logs/`.

### How to verify WITHOUT training?
If you just want to check if the "Red Zones" and "Colors" work:
```bash
python3 src/swarm_sim_pkg/swarm_sim/play_scenario.py
```
This runs a dummy scenario (random actions) purely for you to inspect the visual markers in RViz.

Happy Researching!
