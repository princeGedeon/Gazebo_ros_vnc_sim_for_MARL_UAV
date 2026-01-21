
# Tasks - MARL UAV Coverage Framework

- [ ] **1. Infrastructure Setup**
    - [ ] Create directory structure (`src/envs`, `src/common`, `src/assets`, etc.)
    - [ ] Create `__init__.py` files for python packages.

- [ ] **2. Environment Assets**
    - [ ] Create `src/assets/worlds/city.sdf` with static building blocks.
    - [ ] Update `docker-compose.yml` or `launch` commands to use this world.

- [ ] **3. Core Logic (The Brains)**
    - [ ] Implement `src/common/grid_manager.py` (Coverage tracking).
    - [ ] Implement `src/common/rewards.py` (Reward & Constraint equations).

- [ ] **4. Environments (The Body)**
    - [ ] Implement `src/envs/core/uav_base.py` (ROS 2 interface helper).
    - [ ] Implement `src/envs/single_agent/coverage_env.py` (Gymnasium).
    - [ ] Implement `src/envs/multi_agent/swarm_coverage_env.py` (PettingZoo).

- [ ] **5. Training Scripts**
    - [ ] Create `train_single.py` (Single Agent Baseline).
    - [ ] Create `train_swarm.py` (Multi-Agent PPO).

- [ ] **6. Validation**
    - [ ] Test City world load.
    - [ ] Test Training Loop (Run for 1000 steps).
