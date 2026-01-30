
import numpy as np

class Battery:
    def __init__(self, capacity=100.0, drain_rate=0.1, recharge_rate=2.0):
        self.capacity = capacity
        self.current_level = capacity
        self.drain_rate = drain_rate # per step/movement
        self.recharge_rate = recharge_rate
        
    def consume(self, amount=None):
        cost = amount if amount is not None else self.drain_rate
        self.current_level = max(0.0, self.current_level - cost)
        return self.current_level
        
    def recharge(self):
        self.current_level = min(self.capacity, self.current_level + self.recharge_rate)
        return self.current_level
    
    def reset(self):
        """Restore full battery."""
        self.current_level = self.capacity
        
    def get_percentage(self):
        return self.current_level / self.capacity

    def is_empty(self):
        return self.current_level <= 0.0
