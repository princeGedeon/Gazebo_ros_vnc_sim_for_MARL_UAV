# UAV Swarm MARL for Coverage + SLAM

**Multi-Agent Reinforcement Learning** pour couverture 3D urbaine avec **SLAM multi-robots** décentralisé.

![Architecture](docs/assets/architecture_diagram.png)

---

## 🎯 Objectif

Entraîner un essaim de drones autonomes pour :
- **Coverage 2D** : Maximiser l'exploration d'une zone urbaine
- **SLAM 3D** : Reconstruire une carte 3D collaborative
- **Énergie** : Gestion autonome de batterie avec retour à la base
- **Safety** : Contraintes (NFZ, altitude, collisions) via CBF/Lagrangian

**Architecture Hybride** :
- **RL (2D)** : Action space 3D (vx, vy, yaw) pour coverage optimal
- **SLAM (3D)** : Reconstruction pointcloud avec loop closures
- **Altitude** : Contrôleur PID automatique (Z_optimal = 7.5m)

---

## 🚀 Quick Start

### 1. Installation (Docker)

```bash
# Clone le repo
git clone https://github.com/princeGedeon/Gazebo_ros_vnc_sim_for_MARL_UAV.git
cd Gazebo_ros_vnc_sim_for_MARL_UAV

# Build Docker (avec GPU NVIDIA)
docker build -t uav_swarm_rl .

# Run container
docker run -it --gpus all \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -e DISPLAY=$DISPLAY \
    --name uav_sim \
    uav_swarm_rl
```

### 2. Build ROS2 Workspace

```bash
# Dans le container
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

### 3. Lancer Tout (Auto)
# 🚁 ROS 2 Swarm Simulation (Jazzy + Gazebo Harmonic)

**Multi-Agent Reinforcement Learning (MARL)** environment for UAV Swarm Coverage.
Built with **ROS 2 Jazzy**, **Gazebo Harmonic**, **Ray/RLlib**, and **PettingZoo**.

## 🚀 Quick Start (In 1 Command)

**Launch Simulation + Training + Visualization:**
```bash
./scripts/autolaunch_full.sh case_1
```
*(This starts Gazebo, spawns 3 drones, launches RViz, and starts PPO training)*

## 📊 Dashboard & Visualization

*   **Ray Dashboard (Training Metrics):** [http://localhost:8265](http://localhost:8265)
*   **NoVNC (Gazebo GUI):** [http://localhost:6080](http://localhost:6080)
*   **RViz:** Launched automatically (Dynamic configuration based on drone count).

---

## 📚 Documentation

- **[docs/index.md](docs/index.md)** - Index navigation complète
- **[docs/TECHNICAL_DOCUMENTATION.md](docs/TECHNICAL_DOCUMENTATION.md)** - Architecture détaillée
- **[docs/WHY_2D_NOT_4D.md](docs/WHY_2D_NOT_4D.md)** - Justification architecture (défense)
- **[docs/GNN_COMMUNICATION.md](docs/GNN_COMMUNICATION.md)** - MAGNET GNN pour communication
- **[docs/TRAINING_SCRIPTS_GUIDE.md](docs/TRAINING_SCRIPTS_GUIDE.md)** - Guide scripts training
- **[docs/RVIZ_2D_GRID_SETUP.md](docs/RVIZ_2D_GRID_SETUP.md)** - Config RViz

---

## 🧪 Test & Validation

### Debug Environment

```bash
cd ~/ros2_ws/src/swarm_sim_pkg/swarm_sim/training
python3 debug_rl_env.py
```

**Attendu** : `5/5 tests passed ✅`

### Baseline Aléatoire

```bash
python3 evaluate_policy.py --mode random --episodes 50
```

### Évaluation Trained

```bash
python3 evaluate_policy.py \
    --mode trained \
    --checkpoint outputs/case_1/checkpoint_500000 \
    --episodes 50
```

### Comparaison

```bash
python3 evaluate_policy.py --mode both --checkpoint outputs/case_1/checkpoint_500000
```

**Output** : Graphiques dans `outputs/eval/comparison_*.png`

---

## 🎮 Training Scenarios

### Case 1: MAPPO Simple

```bash
./scripts/autolaunch_full.sh case_1
```

**Caractéristiques** :
- Multi-Agent PPO (MAPPO)
- Reward shaping (coverage + energy)
- 500k timesteps (~3h)

### Case 2: MAPPO + Lagrangian

```bash
./scripts/autolaunch_full.sh case_2
```

**Caractéristiques** :
- Contraintes soft (NFZ, altitude)
- Lagrange multipliers adaptatifs
- Pénalités λ=0.1

### Case 3: MAPPO + CBF

```bash
./scripts/autolaunch_full.sh case_3
```

**Caractéristiques** :
- Control Barrier Functions (hard constraints)
- Safety garantie
- Intervention automatique si violation

---

## 📊 Architecture

### Environment (PettingZoo)

```python
from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv

env = SwarmCoverageEnv(
    num_drones=3,
    max_steps=1000,
    min_height=2.0,
    max_height=12.0,
    nfz_config='default'
)

# Action: [vx, vy, yaw] (3D)
# Observation: [state(14) + lidar(11) + map_local(11×11) + neighbors(3×2)] = 147D
```

### Reward System

```python
r_total = (
    r_coverage_global * 0.3 +      # Objectif global
    r_coverage_incremental * 0.7 + # Exploration locale
    r_energy +                     # Gestion batterie
    r_collision +                  # Pénalité collision
    r_nfz +                        # Pénalité NFZ
    r_altitude +                   # Respect bounds
    r_proximity                    # Éviter autres drones
)
```

### Altitude Controller (PID)

```python
# Z_optimal calculé 1 fois à l'init (sensor_range / 2 = 7.5m)
vz = PID(target=Z_optimal, current=Z_current)
# kp=1.5, kd=0.3

# Cas spécial: descente à Z=0.5m à la station
if distance_to_station < 2.5m:
    vz = PID(target=0.5, current=Z_current)
```

### GNN Communication (MAGNET)

```python
from swarm_sim.models.gnn_communication import MAGNETEncoder

gnn = MAGNETEncoder(obs_dim=147, hidden_dim=128, comm_range=20.0)
enhanced_obs = gnn(observations, positions)  # Message passing
```

**Architecture** :
- Graph Attention Network (GAT) 3 layers
- Communication range : 20m
- PyTorch implementation

---

## 🗺️ Maps & Outputs

### SLAM 3D

**Output** : `outputs/map_episode_X.pcd`  
**Format** : PointCloud (.pcd)  
**Système** : `mrg_slam` (multi-robot graph SLAM)

### Coverage 2D

**Output** : `outputs/coverage_2d_episode_X.npy`  
**Format** : NumPy array (sparse grid)  
**Résolution** : 0.5m

### Visualization

**RViz Topics** :
- `/coverage/global_map` (OccupancyGrid)
- `/coverage/uav_X` (GridCells, couleurs par UAV)
- `/slam/pointcloud` (PointCloud2 3D)

---

## 🔧 Configuration

### Environment Params

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `num_drones` | 3 | Nombre UAVs |
| `max_steps` | 1000 | Steps par épisode |
| `min_height` | 2.0m | Altitude min |
| `max_height` | 12.0m | Altitude max |
| `Z_optimal` | 7.5m | Altitude cruise (auto) |
| `nfz_config` | 'default' | Configuration NFZ |
| `comm_range` | 20.0m | Range GNN |

### Training Params

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `total_timesteps` | 500k | Total steps |
| `checkpoint_freq` | 50k | Fréquence save |
| `lr` | 3e-4 | Learning rate |
| `gamma` | 0.99 | Discount factor |

---

## 📈 Résultats Attendus

| Métrique | Random | Trained (500k) | Amélioration |
|----------|--------|----------------|--------------|
| Episode Return | -100 | +120 | **+220** |
| Coverage (%) | 15% | 65% | **+333%** |
| Battery Efficiency | 0.3 | 0.8 | **+167%** |
| Convergence (steps) | - | 500k | **4× vs 4D** |

---

## 🛠️ Troubleshooting

### Gazebo ne lance pas
```bash
# Vérifier GPU
nvidia-smi

# Relancer
pkill -f gazebo
ros2 launch swarm_sim super_simulation.launch.py
```

### Topics ROS2 manquants
```bash
ros2 topic list | grep -E "(odom|lidar|coverage)"
```

### Environment test échoue
```bash
python3 debug_rl_env.py
# Si fails → voir traceback
```

### Training très lent
→ Vérifier `city_train.sdf` avec `real_time_factor=0.0`

---

## 📦 Structure Projet

```
gazebo_ros2_vnc/
├── README.md                    # Ce fichier
├── docs/                        # Documentation
│   ├── index.md
│   ├── TECHNICAL_DOCUMENTATION.md
│   ├── WHY_2D_NOT_4D.md
│   ├── GNN_COMMUNICATION.md
│   └── TRAINING_SCRIPTS_GUIDE.md
├── scripts/                     # Automation
│   └── autolaunch_full.sh       # Lance tout
├── src/swarm_sim_pkg/
│   └── swarm_sim/
│       ├── envs/                # RL environment
│       │   └── multi_agent/
│       │       └── swarm_coverage_env.py  # PettingZoo env
│       ├── models/              # GNN, policies
│       │   └── gnn_communication.py
│       ├── training/            # Scripts training
│       │   ├── debug_rl_env.py         # Debug complet
│       │   ├── evaluate_policy.py      # Evaluation
│       │   ├── train_mappo.py
│       │   ├── train_mappo_lagrangian.py
│       │   └── train_mappo_cbf.py
│       └── common/              # Utils
│           ├── occupancy_grid_2d.py    # Coverage 2D
│           └── grid_viz_2d.py          # RViz publisher
└── rviz_configs/
    └── full_system.rviz         # Config RViz
```

---

## 🎓 Pour la Défense

**Documents clés** :
1. [WHY_2D_NOT_4D.md](docs/WHY_2D_NOT_4D.md) - Justification architecture
2. [TECHNICAL_DOCUMENTATION.md](docs/TECHNICAL_DOCUMENTATION.md) - Problèmes résolus
3. Graphs comparaison (`outputs/eval/comparison_*.png`)

**Démo** :
```bash
# 1. Validation environnement
python3 debug_rl_env.py  # 5/5 tests

# 2. Baseline
python3 evaluate_policy.py --mode random --episodes 50

# 3. Trained
python3 evaluate_policy.py --mode trained --checkpoint outputs/case_1/checkpoint_500000

# 4. Visualisation RViz
rviz2 -d rviz_configs/full_system.rviz
```

---

## 📝 Citation

```bibtex
@mastersthesis{gedeon2026marl,
  author = {Prince Gedeon},
  title = {Multi-Agent Reinforcement Learning for UAV Swarm Coverage with 3D SLAM},
  school = {Master IAIA},
  year = {2026}
}
```

---

## 📧 Contact

**Auteur** : Prince Gedeon  
**Email** : pgguedje@example.com  
**GitHub** : [princeGedeon](https://github.com/princeGedeon)

---

**Dernière mise à jour** : 2026-01-30  
**Statut** : ✅ Production Ready
