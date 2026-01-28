
import time
import numpy as np
import rclpy
from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv

def play_scenario():
    # 1. Config
    print("Initializing Scenario...")
    env = SwarmCoverageEnv(
        num_drones=3,
        nfz_config='default', # 1 Random Red Zone
        min_height=2.0,
        max_height=10.0,
        max_steps=500
    )
    
    obs, info = env.reset()
    print("Env Reset. Check RViz for:")
    print(" - White Boundary Box")
    print(" - Red Cylinder (NFZ)")
    print(" - Green Spheres (Stations)")
    print(" - Colored Cones (Red, Green, Blue) on Drones")

    try:
        for step in range(500):
            # Random Actions for testing
            actions = {
                agent: env.action_space(agent).sample() * 0.5 # Low speed
                for agent in env.agents
            }
            
            # Step
            obs, rewards, terms, truncs, infos = env.step(actions)
            
            # Slow down for visualization
            time.sleep(0.1) 
            
            if step % 50 == 0:
                print(f"Step {step}: Running...")
                
            if all(terms.values()) or all(truncs.values()):
                print("Episode Finish. Resetting...")
                env.reset()
                
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        env.close()

if __name__ == "__main__":
    play_scenario()
