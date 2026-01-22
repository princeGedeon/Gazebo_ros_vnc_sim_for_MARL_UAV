#!/usr/bin/env python3
import sys
import os
import time
import numpy as np

# Add src to path to find swarm_sim modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../swarm_sim_pkg'))

try:
    from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
except ImportError:
    print("Error: Could not import SwarmCoverageEnv. Make sure you have sourced the ROS 2 workspace.")
    print("Try running: source install/setup.bash")
    sys.exit(1)

def main():
    print("=== Test Rapide de l'Environnement RL (PettingZoo) ===")
    
    # Configuration des Stations (Test de la fonctionnalité demandée)
    stations = [[5.0, 5.0], [-5.0, -5.0]] 
    
    # Initialisation
    print("1. Initialisation de l'environnement...")
    env = SwarmCoverageEnv(num_drones=3, station_config=stations)
    
    # Reset
    print("2. Reset de l'environnement...")
    observations, infos = env.reset(seed=42)
    print(f"   Drones actifs: {env.agents}")
    
    # Boucle de Test
    print("3. Boucle d'interaction (100 steps)...")
    for step in range(100):
        # Actions Aléatoires (Remplacer par votre Agent RL ici)
        actions = {agent: env.action_space(agent).sample() for agent in env.agents}
        
        # Step
        observations, rewards, terminations, truncations, infos = env.step(actions)
        
        # Affichage
        if step % 10 == 0:
            print(f"   [Step {step}] Rewards: {rewards}")
        
        # Simulation d'un délai (pour voir ce qui se passe si on regarde la Simu)
        time.sleep(0.1)

    # Sauvegarde de la Carte (Fonctionnalité IGN)
    print("4. Test de sauvegarde de la carte...")
    # Ensure directory exists in case CWD is weird
    output_path = "src/swarm_sim_pkg/swarm_sim/outputs/debug_map.npy"
    if not os.path.exists(os.path.dirname(output_path)):
         # Fallback to local outputs if path doesn't exist
         output_path = "outputs/debug_map.npy"
         
    env.save_occupancy_map(output_path)
    
    # Close
    env.close()
    print("=== Test Terminé avec Succès ===")

if __name__ == "__main__":
    main()
