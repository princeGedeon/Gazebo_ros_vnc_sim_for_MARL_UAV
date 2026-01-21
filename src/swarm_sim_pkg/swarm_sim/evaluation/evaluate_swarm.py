
import os
import time
import numpy as np
import supersuit as ss
from stable_baselines3 import PPO
from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv

def evaluate():
    print("============================================")
    print("   Swarm Evaluation (Sim + RL + Mapping)    ")
    print("============================================")
    
    # Paths
    model_path = "ppo_swarm_coverage" # Assumes trained model exists
    if not os.path.exists(model_path + ".zip"):
         print(f"Error: Model {model_path} not found. Run train_swarm.py first.")
         # Fallback to random for demonstration if no model
         model = None
    else:
         model = PPO.load(model_path)
         print(f"Loaded Model: {model_path}")

    # Env Setup (Visual Mode)
    env = SwarmCoverageEnv(num_drones=3, render_mode='human')
    
    # Wrappers (Must match training!)
    env = ss.pettingzoo_env_to_vec_env_v1(env)
    env = ss.concat_vec_envs_v1(env, num_vec_envs=1, num_cpus=1, base_class='stable_baselines3')

    obs = env.reset()
    done = False
    total_reward = 0
    steps = 0
    
    # Experiment Logs
    log_dir = "evaluation_results"
    os.makedirs(log_dir, exist_ok=True)
    
    print("Starting Evaluation Run...")
    while not done:
        if model:
            action, _ = model.predict(obs)
        else:
            action = [env.action_space.sample()] # Random
            
        obs, reward, done, info = env.step(action)
        total_reward += reward
        steps += 1
        
        # Interactive delay
        time.sleep(0.05)
        
        if steps % 100 == 0:
            print(f"Step {steps} | Reward: {reward}")

    print("============================================")
    print(f"Episode Finished.")
    print(f"Total Steps: {steps}")
    print(f"Total Reward: {total_reward}")
    
    # Save Metrics
    with open(f"{log_dir}/metrics.txt", "w") as f:
        f.write(f"Steps: {steps}\n")
        f.write(f"Total Reward: {total_reward}\n")
        f.write(f"Model: {model_path}\n")
        
    print(f"Results saved to {log_dir}/metrics.txt")
    
    env.close()

if __name__ == "__main__":
    evaluate()
