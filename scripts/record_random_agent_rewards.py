#!/usr/bin/env python3
import sys
import os
import time
import csv
import numpy as np
import rclpy

# Add src to path to find swarm_sim modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../src/swarm_sim_pkg'))

try:
    from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
except ImportError:
    print("Error: Could not import SwarmCoverageEnv. Make sure you have sourced the ROS 2 workspace.")
    print("Try running: source install/setup.bash")
    sys.exit(1)

def main():
    print("=== Enregistrement des Rewards (Random Agent) ===")
    
    # 1. Output File Setup
    output_dir = "outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    csv_filename = os.path.join(output_dir, "random_rewards.csv")
    
    # 2. Init Environment
    print("1. Initialisation de l'environnement (3 UAVs)...")
    env = SwarmCoverageEnv(num_drones=3)
    
    observations, infos = env.reset(seed=42)
    
    # 3. CSV Header
    # We will log: Step, Agent, TotalReward, Collision, Energy, Coverage, SafetyCost
    headers = ["Step", "Agent", "TotalReward", "Collision", "Energy", "Coverage", "WallClockTime"]
    
    print(f"2. Simulation & Enregistrement dans: {csv_filename}")
    
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        
        start_time = time.time()
        
        # 4. Loop
        MAX_STEPS = 1000
        print(f"3. Lancement de {MAX_STEPS} steps...")
        
        for step in range(MAX_STEPS):
            # Random Actions
            actions = {agent: env.action_space(agent).sample() for agent in env.agents}
            
            # Step
            observations, rewards, terminations, truncations, infos = env.step(actions)
            
            current_time = time.time() - start_time
            
            # Log Data
            for agent in env.agents:
                rew = rewards.get(agent, 0.0)
                info = infos.get(agent, {})
                
                # Extract breakdown if available (from previous modification)
                # Note: infos might just have direct values depending on implementation
                # Let's rely on what we saw in debug_rl_env.py analysis or just standard keys
                
                collision = 1 if info.get("collision", False) else 0
                
                # Extract components if available in r_breakdown, else 0
                r_breakdown = info.get("r_breakdown", {})
                r_energy = r_breakdown.get("energy", 0.0)
                r_coverage = r_breakdown.get("cov", 0.0)
                
                # Write Row
                writer.writerow([step, agent, f"{rew:.4f}", collision, f"{r_energy:.4f}", f"{r_coverage:.4f}", f"{current_time:.2f}"])
            
            # Console Progress
            if step % 50 == 0:
                print(f"   Step {step}/{MAX_STEPS} | Time: {current_time:.1f}s")
                
            # Rate Limit (optional, to mimic real-time or run fast)
            # time.sleep(0.01) 
            
    print(f"=== Terminé. Fichier sauvegardé: {csv_filename} ===")
    print("Vous pouvez analyser ce fichier avec Excel ou Python (pandas).")
    
    env.close()

if __name__ == "__main__":
    main()
