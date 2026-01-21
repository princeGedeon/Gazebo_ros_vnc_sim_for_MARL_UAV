
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import rclpy
import sys
import os

from swarm_sim.common.voxel_manager import VoxelManager
from swarm_sim.common.rewards import RewardEngine
from swarm_sim.envs.core.uav_base import UAVBase

class CoverageEnv(gym.Env):
    """
    Gymnasium Env for Single-UAV 3D Volumetric Coverage.
    """
    metadata = {"render_modes": ["human"], "name": "uav_coverage_v0"}

    def __init__(self, render_mode=None):
        super().__init__()
        
        # 1. Config
        self.grid_res = 1.0
        self.map_size = 20 # -20 to 20
        self.height_range = (0, 10)
        self.max_steps = 1000
        
        # 2. Logic Modules
        self.voxel_manager = VoxelManager(x_range=(-self.map_size, self.map_size), 
                                      y_range=(-self.map_size, self.map_size),
                                      z_range=self.height_range,
                                      resolution=self.grid_res)
        self.reward_engine = RewardEngine()
        
        # 3. Space Definitions
        # Action: Velocity [vx, vy, vz, wz]
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
        
        # Observation:
        # - Agent State (6): Pos, Vel
        # - Lidar (16): Downsampled rays
        # - Local Voxel Grid (7x7x5 patch flattened): 245
        #   (radius_xy=3 -> width 7, radius_z=2 -> height 5)
        self.local_map_dim = (7 * 7 * 5)
        obs_dim = 6 + 16 + self.local_map_dim
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32)

        # 4. ROS Setup
        if not rclpy.ok():
            rclpy.init()
        self.node = rclpy.create_node("coverage_gym_node")
        
        # Assuming model name 'X1' for single agent
        self.uav = UAVBase(self.node, agent_id="X1", namespace="model")
        
        self.current_step = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.voxel_manager.reset()
        
        # TODO: Calls to Gazebo Reset Service would go here
        
        # Wait for state update
        rclpy.spin_once(self.node, timeout_sec=0.1)
        
        return self._get_obs(), {}

    def step(self, action):
        self.current_step += 1
        
        self.uav.apply_action(action)
        
        # Step Simulation
        rclpy.spin_once(self.node, timeout_sec=0.1)
        
        # Logic
        pos = self.uav.position
        new_cells = self.voxel_manager.update([pos])
        
        # Calculate Reward
        lidar_min = np.min(self.uav.lidar_ranges) if len(self.uav.lidar_ranges) > 0 else 10.0
        collision = lidar_min < 0.3
        
        reward = self.reward_engine.compute_reward(new_cells, collision, self.current_step)
        constraints = self.reward_engine.check_constraints(pos, lidar_min)
        
        # Obs
        obs = self._get_obs()
        
        # Termination
        terminated = False
        truncated = self.current_step >= self.max_steps
        
        if collision:
            terminated = True
        
        info = {
            "coverage_ratio": self.voxel_manager.get_coverage_ratio(),
            "constraints": constraints
        }
        
        return obs, reward, terminated, truncated, info

    def _get_obs(self):
        # 1. State
        state = self.uav.get_state()
        
        # 2. Lidar (Downsample 360 -> 16)
        scan = self.uav.lidar_ranges
        if len(scan) == 360:
            scan_ds = np.mean(scan.reshape(-1, 360//16), axis=1)
        else:
            scan_ds = np.zeros(16)
        
        # 3. Voxel Patch
        patch = self.voxel_manager.get_observation(state[0], state[1], state[2], r_xy=3, r_z=2)
        patch_flat = patch.flatten()
        
        return np.concatenate([state, scan_ds, patch_flat]).astype(np.float32)

    def close(self):
        self.node.destroy_node()
        rclpy.shutdown()
