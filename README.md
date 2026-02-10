# Multi-Agent UAV Swarm: Navigation & SLAM (Thesis Project)

**Multi-Agent Reinforcement Learning (MARL)** simulation for UAV Swarm Navigation, Collision Avoidance, and **Collaborative Graph SLAM**.

![System Architecture](https://img.shields.io/badge/Architecture-Distributed-blue)
![Status](https://img.shields.io/badge/Status-Research_Prototype-orange)
![Docker](https://img.shields.io/badge/Docker-CPU_%2F_GPU-green)

---

## 🎯 Project Overview

This research platform integrates **ROS 2 Jazzy**, **Gazebo Harmonic**, and **Ray RLLib** to train autonomous drone swarms. It addresses three key challenges:
1.  **Distributed Navigation**: Agents learn to fly to targets without communicating global maps.
2.  **Safety Guarantees**: Comparing Lagrangian Relaxation vs. Control Barrier Functions (CBF).
3.  **Collaborative Mapping**: Real-time merging of maps using Multi-Robot Graph SLAM.

---

## 🚀 Quick Start (Docker)

The entire environment is containerized. You do not need to install ROS 2 locally.

### 1. Prerequisites
*   **Docker** & **Docker Compose**
*   **Disk Space**: At least **15 GB** free (ML libraries & Gazebo are heavy).

### 2. Launch
Clone the repo and start the containers.
```bash
# 1. Start the Stack (Builds image automatically)
# Note: For CPU-only users, ensure 'runtime: nvidia' is commented out in docker-compose.yml
sudo docker compose up --build
```
*   **`sim` container**: Runs Gazebo, RLLib Training, and VNC Server.
*   **`slam` container**: Runs the Multi-Robot Graph SLAM algorithm.

### 3. Visualization
Once running, you can monitor the system via browser:
*   **Gazebo View (NoVNC)**: [http://localhost:6080](http://localhost:6080)
*   **Training Metrics (Ray Dashboard)**: [http://localhost:8265](http://localhost:8265)
*   **TensorBoard**: [http://localhost:6006](http://localhost:6006) (See *Visualization Guide*)

---

## 📚 Documentation Framework

Access the detailed documentation in the `docs/` folder:

| Document | Content |
| :--- | :--- |
| **[📂 Architecture](docs/architecture.md)** | System overview, Docker split, and **Why 2.5D Mapping?** |
| **[🎓 Thesis Materials](docs/thesis_materials.md)** | Methodology, Challenges (State Space Explosion), and **Defense Strategy**. |
| **[🧠 Training Guide](docs/training_guide.md)** | RL Environment, Rewards, Action Space, and **"1 Month Training" Reality**. |
| **[📈 Math Model](docs/math_model_convergence.md)** | MAPPO, Lagrangian Dual Ascent, and CBF Proofs. |
| **[📊 Visualization](docs/visualization_guide.md)** | How to use TensorBoard and RViz to interpret results. |

---

## 🎮 Advanced Usage: Multi-Drone & Teleop

### 1. Multi-Drone Launch
To launch the full environment with 3 drones, SLAM, and visualizers without training:
```bash
./scripts/launch_all.sh train
# OR directly via ROS 2
ros2 launch swarm_sim super_simulation.launch.py
```

### 2. Teleoperation (Manual Control)
You can manually control each drone using your keyboard. You need to open **3 separate terminals** inside the container (`docker exec -it rosette_sim bash`):

**Terminal 1 (Drone 0):**
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/uav_0/cmd_vel
```

**Terminal 2 (Drone 1):**
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/uav_1/cmd_vel
```

**Terminal 3 (Drone 2):**
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/uav_2/cmd_vel
```
*Keys: `i` (forward), `k` (stop), `j` (left), `l` (right).*

### 3. Random Agent & Debugging (1000 Actions)
To test the environment, constraints, and see rewards/penalties in real-time without training:
```bash
python3 scripts/debug_rl_env.py
```
**What you will see:**
*   Drones performing random actions for 1000 steps.
*   **Real-time logs** of Rewards, No-Fly Zone (NFZ) violations, and Crashes.
*   Breakdown of rewards (Coverage, Safety, Battery).

---

## 🎮 Running Training Experiments

Scripts are located in `scripts/`. You can run them inside the container (`docker exec -it rosette_sim bash`).

### Case 1: Simple Navigation (Baseline)
```bash
./scripts/train_case_1_simple.sh
```
*Goal*: Point-to-point flight. No complex safety constraints.

### Case 2: Safe RL (Lagrangian)
```bash
./scripts/train_case_2_lagrange.sh
```
*Goal*: Learn to respect safety boundaries (collisions) via adaptive penalties.

### Case 3: Hard Safety (CBF)
```bash
./scripts/train_case_3_cbf.sh
```
*Goal*: Guarantee safety using Control Barrier Functions (QP Solver).

---

## 🔧 Troubleshooting

### 1. `no space left on device`
Docker builds are large.
*   **Fix**: Run `sudo docker system prune -a -f` to clean old images.
*   **Fix**: Ensure your `Dockerfile` uses `pip install --no-cache-dir`.

### 2. `invalid runtime name: nvidia`
You are running on a machine without an NVIDIA GPU (or without the Container Toolkit).
*   **Fix**: Open `docker-compose.yml` and comment out `runtime: nvidia` and the `environment` section for NVIDIA variables.

### 3. Build fails on `vcs import`
*   **Fix**: Ensure `src/Multi-Robot-Graph-SLAM` is not empty. If it is, clone the repo manually:
    ```bash
    git clone https://github.com/aserbremen/Multi-Robot-Graph-SLAM src/Multi-Robot-Graph-SLAM
    ```

---

## 📝 Citation

If you use this platform for your thesis:
```bibtex
@mastersthesis{gedeon2026marl,
  author = {Prince Gedeon},
  title = {Multi-Agent Reinforcement Learning for UAV Swarm Coverage with 3D SLAM},
  school = {Master IAIA},
  year = {2026}
}
```
