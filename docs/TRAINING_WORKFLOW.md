
# 🚁 UAV Swarm Training Workflow

## 1. Environment Setup

Ensure you are using the `rosette_swarm` container.

### Build the Package
```bash
cd /root/ros2_ws
colcon build --packages-select swarm_sim --symlink-install
source install/setup.bash
```

## 2. Running Training

We have provided entry points for training:

### Single Agent (PPO)
```bash
ros2 run swarm_sim train_single
```
*Note: This will try to connect to a running Gazebo instance or spin one up if we integrate the launcher.*
*Currently, `train_single.py` initiates the ROS node but **expects Gazebo to be running** separately mostly.*

### Multi-Agent Swarm (MAPPO via Parameter Sharing)
```bash
ros2 run swarm_sim train_swarm
```

## 3. Launching the Simulation

To visualize the environment while training:

```bash
# Terminal 1
ros2 launch swarm_sim simulation.launch.py

# Terminal 2
ros2 run swarm_sim train_swarm
```

## 4. Constraint-Aware MARL (Roadmap)

The current setup uses `rewards.py` to calculate constraint violations (collisions).
To implement **MAPPO-Lagrangian**:
1. Modify `train_swarm.py`.
2. Instead of standard `PPO` from SB3, use a constrained policy optimizer (e.g. from `safe-reinforcement-learning` or custom implementation).
3. The `info` dictionary from `SwarmCoverageEnv` already contains `constraints` data needed for the cost value limits.
