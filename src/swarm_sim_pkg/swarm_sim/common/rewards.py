
import numpy as np

class RewardEngine:
    """
    Calculates rewards and constraint violations for UAV tasks.
    """
    def __init__(self, config=None):
        self.config = config or {}
        
        # Weights
        self.w_coverage = self.config.get("w_coverage", 5.0)
        self.w_time = self.config.get("w_time", -0.05)
        self.w_collision = self.config.get("w_collision", -10.0)
        
        # Constraints
        self.min_height = 0.5
        self.max_height = 10.0
        self.safe_distance = 1.0 # Meters to obstacle

    def compute_reward(self, new_cells, collision_occured, step_count):
        reward = 0.0
        
        # 1. Coverage Reward
        reward += new_cells * self.w_coverage
        
        # 2. Time Penalty (encourage efficiency)
        reward += self.w_time
        
        # 3. Collision Penalty (Soft constraint)
        if collision_occured:
            reward += self.w_collision
            
        return reward

    def check_constraints(self, pos, lidar_min_dist):
        """
        Returns a dictionary of constraint costs (Cost > 0 means violation).
        Used for Constrained MARL.
        """
        x, y, z = pos
        costs = {
            "collision": 0.0,
            "boundary": 0.0
        }
        
        # Collision Constraint
        # Example: Cost = 1 if too close, else 0
        if lidar_min_dist < self.safe_distance:
            costs["collision"] = 1.0
            
        # Height/Boundary Constraint
        if z < self.min_height or z > self.max_height:
             costs["boundary"] = 1.0
             
        return costs
