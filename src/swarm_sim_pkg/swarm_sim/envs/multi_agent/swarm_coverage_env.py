
from pettingzoo import ParallelEnv
from gymnasium import spaces
import numpy as np
import rclpy
import sys
import os

from swarm_sim.common.voxel_manager import VoxelManager
from swarm_sim.common.rewards import RewardEngine
from swarm_sim.envs.core.uav_base import UAVBase
from swarm_sim.common.viz_utils import VoxelVisualizer

class SwarmCoverageEnv(ParallelEnv):
    """
    PettingZoo Parallel Env for Multi-UAV Cooperative 3D Coverage.
    """
    metadata = {"render_modes": ["human"], "name": "swarm_coverage_v0"}

    def __init__(self, num_drones=3):
        self.num_drones = num_drones
        self.possible_agents = [f"uav_{i}" for i in range(self.num_drones)]
        self.agents = self.possible_agents[:]
        
        # 1. Logic
        # Global Truth (for evaluation/global reward)
        self.global_map = VoxelManager(x_range=(-20, 20), y_range=(-20, 20), z_range=(0,10))
        
        # Local Beliefs (Decentralized)
        self.local_maps = {
            agent: VoxelManager(x_range=(-20, 20), y_range=(-20, 20), z_range=(0,10))
            for agent in self.possible_agents
        }
        
        self.reward_engine = RewardEngine()
        
        # 2. Spaces
        # Action: Velocity
        self.action_spaces = {
            agent: spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
            for agent in self.possible_agents
        }
        
        # Observation: Same as single agent (Local 3D Map)
        self.local_map_dim = (7 * 7 * 5)
        # Obs: state(6+1) + lidar(16) + map + imu(6) + neighbors(num_drones)
        obs_dim = 7 + 16 + self.local_map_dim + 6 + self.num_drones
        self.observation_spaces = {
            agent: spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32)
            for agent in self.possible_agents
        }
        
        # 3. ROS
        if not rclpy.ok():
            rclpy.init()
        self.node = rclpy.create_node("swarm_coverage_node")
        self.viz = VoxelVisualizer()
        
        # Ground Stations (Must match Launch file)
        # We could pass this as arg or config, for now hardcoded matches
        self.station_positions = np.array([
            [5.0, 5.0], [-5.0, 5.0], [5.0, -5.0], [-5.0, -5.0],
            [10.0, 0.0], [-10.0, 0.0], [0.0, 10.0], [0.0, -10.0]
        ])
        # Active stations count (default 1, should match launch arg usually)
        # But we can just "simulate" all of them being valid pads.
        
        self.uavs = {}
        for agent in self.possible_agents:
            # Assuming model names are uav_0, uav_1... in Gazebo
            self.uavs[agent] = UAVBase(self.node, agent_id=agent, namespace="")

    def reset(self, seed=None, options=None):
        self.agents = self.possible_agents[:]
        self.global_map.reset()
        for m in self.local_maps.values():
            m.reset()
        self.step_count = 0
        
        # Wait for data
        rclpy.spin_once(self.node, timeout_sec=0.1)
        
        # Detailed Logging (User Request)
        print(f"\n[SwarmEnv] Reset Complete using Seed: {seed}")
        print(f"[SwarmEnv] Active Drones: {self.num_drones} | Agents: {self.possible_agents}")
        print(f"[SwarmEnv] Map Config: {self.global_map.__class__.__name__} | Bounds: {self.global_map.x_range}")
        print(f"[SwarmEnv] Ground Stations: {len(self.station_positions)} active locations.")
        
        observations = {agent: self._get_obs(agent) for agent in self.agents}
        infos = {agent: {} for agent in self.agents}
        
        return observations, infos

    def step(self, actions):
        self.step_count += 1
        
        # Apply Actions
        for agent, action in actions.items():
            if agent in self.uavs:
                self.uavs[agent].apply_action(action)
                
        # Step World
        rclpy.spin_once(self.node, timeout_sec=0.1)
        
        # Update Logic
        # Update Logic
        # 1. Update each agent's local map and the global map
        uav_positions = {}
        for agent in self.agents:
            pos = self.uavs[agent].position
            uav_positions[agent] = pos
            # Update Local
            self.local_maps[agent].update([pos])
            # Update Global
            self.global_map.update([pos])

        # 2. Decentralized Map Merging (Swarm-SLAM Logic)
        # Verify connectivity
        comm_range = 5.0 # meters
        merged_pairs = []
        
        agent_ids = self.agents
        for i in range(len(agent_ids)):
            for j in range(i + 1, len(agent_ids)):
                id1, id2 = agent_ids[i], agent_ids[j]
                pos1 = uav_positions[id1]
                pos2 = uav_positions[id2]
                
                dist = np.linalg.norm(pos1 - pos2)
                if dist < comm_range:
                    # CONTACT! Exchange Maps
                    # Merge Logic: Map A |= Map B
                    new_for_1 = self.local_maps[id1].merge_from(self.local_maps[id2])
                    new_for_2 = self.local_maps[id2].merge_from(self.local_maps[id1])
                    merged_pairs.append((id1, id2))

        # Cooperative coverage: Global gain
        # We calculate global new cells by tracking global map changes
        # But for RL reward, we often use the *Global* progress to encourage teamwork
        
        new_cells = self.global_map.visited_count # This is total, need delta? 
        # Actually in previous code 'update' returned delta.
        # Let's trust global map delta logic if we kept it.
        # For simplicity, let's recalculate delta manually or assume Step-Based reward mechanism
        # Simpler: Reward = Count of (Global Map - Previous Global Map)
        # But we didn't store previous.
        # Let's stick to the previous 'update' return value if we can, or just use current coverage count.
        
        # Re-calc delta from global map isn't easy unless we stored old count.
        # Let's modify VoxelManager to return delta on update? Yes it does.
        # Wait, I called update([pos]) above individually.
        # We need to sum them up or track total.
        
        current_global_count = self.global_map.visited_count
        # Hack: We need a prev_count property in env to calc delta
        if not hasattr(self, 'prev_global_count'): self.prev_global_count = 0
        
        delta_cells = current_global_count - self.prev_global_count
        self.prev_global_count = current_global_count
        
        
        # Global Coverage Reward (Total new cells this step for the TEAM)
        cov_reward_total = delta_cells * 5.0
        # Shared equally or individually? User asked for "objectifs global coverage"
        # Let's give team reward to all
        r_team_coverage = cov_reward_total / len(self.agents)

        rewards = {}
        terminations = {}
        truncations = {}
        infos = {}
        
        for agent in self.agents:
            uav = self.uavs[agent]
            lidar_min = np.min(uav.lidar_ranges) if len(uav.lidar_ranges) > 0 else 10.0
            
            # 1. Collision (Strong Penalty)
            collision = lidar_min < 0.3
            r_collision = -100.0 if collision else 0.0
            
            # 2. Battery & RTB Logic
            bat_level = uav.battery.get_percentage() # 0.0 to 1.0
            r_energy = 0.0
            
            # Find nearest station
            uav_pos_2d = uav.position[:2]
            dists = np.linalg.norm(self.station_positions - uav_pos_2d, axis=1)
            min_dist = np.min(dists)
            
            # Check if moving while critical
            is_moving = np.linalg.norm(uav.velocity) > 0.1
            if bat_level < 0.2:
                # Incentive to Return to Nearest Base
                r_energy -= (min_dist * 0.1) # Penalty for being far from NEAREST base
                
                if bat_level < 0.05 and is_moving:
                    r_energy -= 10.0 # Critical penalty for moving when dead
            
            # Recharge logic
            self._check_recharge(uav)
            
            # 3. Decentralized Loop Closure Sharing
            neighbors = self._get_neighbors(agent)
            # Find neighbors < 3m (excluding self=0)
            close_mask = (neighbors > 0) & (neighbors < 3.0)
            if np.any(close_mask):
                # Mock "Map Merge" - in reality, we assume this improves map quality
                # We give a small bonus for successful communication/rendezvous
                r_loop_closure = 1.0 
                # Here is where you'd call: self.shared_map.merge(agent_i, agent_j)
            else:
                r_loop_closure = 0.0
            
            r_time = -0.05
            
            # 4. Total Reward
            total_reward = r_team_coverage + r_time + r_collision + r_energy + r_loop_closure
            rewards[agent] = total_reward
            
            # Termination: Collision OR Dead Battery
            terminations[agent] = collision or (bat_level <= 0.0)
            truncations[agent] = self.step_count >= 1000
            
            # Info for Debug/Logging
            infos[agent] = {
                "collision": collision,
                "coverage": self.local_maps[agent].get_coverage_ratio(),
                "global_coverage": self.global_map.get_coverage_ratio(),
                "battery": bat_level,
                "r_breakdown": {
                    "cov": r_team_coverage,
                    "col": r_collision,
                    "energy": r_energy,
                    "loop": r_loop_closure
                }
            }
            
            # --- REAL-TIME LOGGING (User Request) ---
            # Print status every step (or every N steps)
            if self.step_count % 5 == 0: 
                print(f"[{agent} | Step {self.step_count}] "
                      f"Bat: {bat_level*100:.1f}% | "
                      f"Pos: {np.round(uav.position, 1)} | "
                      f"Rew: {total_reward:.2f} "
                      f"(Cov:{r_team_coverage:.2f} Col:{r_collision:.0f} Eny:{r_energy:.2f} Loop:{r_loop_closure:.0f})")
                if collision:
                    print(f"!!! [{agent}] CRITICAL: COLLISION DETECTED !!!")
                if bat_level < 0.2:
                    print(f"!!! [{agent}] WARNING: BATTERY LOW (RTB Penalty Applied) !!!")
        
        if any(terminations.values()):
            for a in self.agents: terminations[a] = True
            
        # Visualization (RViz) - Publish Global Truth for Debug
        if self.step_count % 10 == 0: 
             self.viz.publish_voxels(self.global_map.grid, 
                                   self.global_map.resolution,
                                   self.global_map.x_min,
                                   self.global_map.y_min,
                                   self.global_map.z_min)
            
        return observations, rewards, terminations, truncations, infos

    def _check_recharge(self, uav):
        uav_pos_2d = uav.position[:2]
        # Check distance to ALL known stations
        dists = np.linalg.norm(self.station_positions - uav_pos_2d, axis=1)
        if np.any(dists < 1.0):
            uav.battery.recharge()

    def _get_neighbors(self, uav_id):
        # Returns distance vector to other agents
        me = self.uavs[uav_id].position
        dists = []
        for other_id in self.possible_agents:
            if other_id == uav_id:
                dists.append(0.0)
            else:
                dists.append(np.linalg.norm(me - self.uavs[other_id].position))
        return np.array(dists)

    def _get_obs(self, agent):
        uav = self.uavs[agent]
        state = uav.get_state() # now includes battery
        
        # Lidar
        scan = uav.lidar_ranges
        if len(scan) == 360:
            scan_ds = np.mean(scan.reshape(-1, 360//16), axis=1)
        else:
            scan_ds = np.zeros(16)
            
        # Voxel Patch from LOCAL map
        patch = self.local_maps[agent].get_observation(state[0], state[1], state[2], r_xy=3, r_z=2)
        patch_flat = patch.flatten()
        
        neighbors = self._get_neighbors(agent)
        imu = uav.imu_data
        
        return np.concatenate([state, scan_ds, patch_flat, imu, neighbors]).astype(np.float32)

    def close(self):
        self.node.destroy_node()
        rclpy.shutdown()
