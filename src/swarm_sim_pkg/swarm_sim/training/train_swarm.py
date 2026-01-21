
import supersuit as ss
from stable_baselines3 import PPO
from stable_baselines3.ppo import PROXY_PPO # Might be needed for some versions, or just PPO
import os
import sys

# When installed as a package, we import from swarm_sim
from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv

def main():
    print("Initializing Swarm Coverage Task (MARL)...")
    
    # 1. Create Env
    env = SwarmCoverageEnv(num_drones=3)
    
    # 2. Wrappers for SB3 compatibility (Parameter Sharing)
    # Convert ParallelEnv -> VectorEnv
    env = ss.pettingzoo_env_to_vec_env_v1(env)
    
    # Concatenate for SB3 (handles multiple agents as a batch)
    env = ss.concat_vec_envs_v1(env, num_vec_envs=1, num_cpus=1, base_class='stable_baselines3')
    
    # 3. Model
    # Since observation space is uniform, we can use standard PPO (Parameter Sharing)
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./logs/swarm_coverage/")
    
    # 4. Train
    print("Starting Swarm Training (20k steps)...")
    model.learn(total_timesteps=20000)
    
    # 5. Save
    model.save("ppo_swarm_coverage")
    print("Model Saved.")
    
    env.close()

if __name__ == "__main__":
    main()
