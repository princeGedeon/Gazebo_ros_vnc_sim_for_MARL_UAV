
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
    # 3. Model
    # Since observation space is uniform, we can use standard PPO (Parameter Sharing)
    # Logs validation: src/swarm_sim_pkg/swarm_sim/logs
    log_path = os.path.abspath("src/swarm_sim_pkg/swarm_sim/logs")
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=log_path)
    
    # 4. Train
    print("Starting Swarm Training (100k steps)...")
    print(f"Monitor training with: tensorboard --logdir {log_path}")
    print("Real-time Visualization: Open RViz -> /coverage_map_voxels")
    model.learn(total_timesteps=100000)
    
    # 5. Save
    model_dir = os.path.abspath("src/swarm_sim_pkg/swarm_sim/models")
    os.makedirs(model_dir, exist_ok=True)
    save_path = os.path.join(model_dir, "ppo_swarm_coverage")
    model.save(save_path)
    print(f"Model Saved to {save_path}")
    
    env.close()

if __name__ == "__main__":
    main()
