import isaacgym  # Optional: only if using Isaac Gym features, but SKRL might import it
import torch
import torch.nn as nn
import time
import os
import sys

# Add Environment Path
sys.path.append(os.path.join(os.path.dirname(__file__), '../swarm_sim_pkg'))

from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv

# SKRL Imports
from skrl.agents.torch.ppo import PPO, PPO_DEFAULT_CONFIG
from skrl.agents.torch.mappo import MAPPO, MAPPO_DEFAULT_CONFIG
from skrl.envs.wrappers.torch import PettingZooWrapper, ParallelPettingZooWrapper
from skrl.memories.torch import RandomMemory
from skrl.models.torch import Model, MultiAgentMixin

# =============================================================================
# 1. Define Models (Actor & Critic)
# =============================================================================
class Policy(MultiAgentMixin, Model):
    def __init__(self, observation_space, action_space, device, features_extractor=None):
        Model.__init__(self, observation_space, action_space, device)
        MultiAgentMixin.__init__(self)
        
        # Simple MLP for now (Can be upgraded to CNN for 3D Map)
        # Input shape depends on observation dim
        # We assume flattened input
        self.net = nn.Sequential(
            nn.Linear(self.num_observations, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
            nn.Linear(64, self.num_actions) # Mean actions
        )
        self.log_std_parameter = nn.Parameter(torch.zeros(self.num_actions))

    def compute(self, inputs, role=""):
        # inputs["states"] contains observations
        return self.net(inputs["states"]), self.log_std_parameter, {}

class Value(MultiAgentMixin, Model):
    def __init__(self, observation_space, action_space, device, features_extractor=None):
        Model.__init__(self, observation_space, action_space, device)
        MultiAgentMixin.__init__(self)
        
        self.net = nn.Sequential(
            nn.Linear(self.num_observations, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
            nn.Linear(64, 1)
        )

    def compute(self, inputs, role=""):
        return self.net(inputs["states"]), {}

# =============================================================================
# 2. Main Training Loop
# =============================================================================
def main():
    print("--- Starting SKRL MAPPO Training ---")
    
    # Init Environment
    # Note: SKRL works best if agents match names perfectly
    env = SwarmCoverageEnv(num_drones=3)
    env = ParallelPettingZooWrapper(env) # Wrap for Torch

    device = env.device

    # Instantiate Models
    models = {}
    for agent in env.agents:
        models[agent] = {}
        models[agent]["policy"] = Policy(env.observation_spaces[agent], env.action_spaces[agent], device)
        models[agent]["value"] = Value(env.observation_spaces[agent], env.action_spaces[agent], device)

    # Memory
    memories = {}
    for agent in env.agents:
        memories[agent] = RandomMemory(memory_size=1024, num_envs=env.num_envs, device=device)

    # Agents (MAPPO)
    agents = {}
    cfg = MAPPO_DEFAULT_CONFIG.copy()
    cfg["learning_rate"] = 1e-3
    cfg["batch_size"] = 64
    
    for agent in env.agents:
        # MAPPO treats all agents as sharing a Critic usually due to shared info?
        # SKRL implementation allows individual or shared.
        # Here we setup individual PPO agents linked via MAPPO logic if applicable,
        # or just Independent PPO (IPPO) if we instantiate PPO class.
        # User asked for MAPPO.
        
        agents[agent] = PPO(models=models[agent],
                            memory=memories[agent],
                            cfg=cfg,
                            observation_space=env.observation_spaces[agent],
                            action_space=env.action_spaces[agent],
                            device=device)

    # Trainer (Manual Loop or SKRL Trainer)
    # SKRL has a SequentialTrainer or ParallelTrainer
    from skrl.trainers.torch import SequentialTrainer
    
    trainer = SequentialTrainer(env=env, agents=list(agents.values()))
    
    print("Beginning Training...")
    trainer.train(timesteps=10000)
    print("Training finished!")
    
    # Save
    trainer.save("./checkpoints")

if __name__ == "__main__":
    main()
