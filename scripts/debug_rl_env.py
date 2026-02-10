#!/usr/bin/env python3
import sys
import os
import time
import numpy as np
import rclpy

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

    # --- WAIT FOR SIMULATION ---
    print("   [INFO] Attente de la première pose (Odométrie)...")
    print("   ⚠️  IMPORTANT: Assurez-vous que Gazebo est lancé dans un autre terminal !")
    print("      (Commande: ./scripts/launch_all.sh train  OU  ros2 launch swarm_sim super_simulation.launch.py)")
    
    # Simple Wait Loop
    wait_steps = 0
    uav0 = env.uavs['uav_0']
    while np.allclose(uav0.position, 0) and wait_steps < 50:
         rclpy.spin_once(env.node, timeout_sec=0.1)
         wait_steps += 1
         
    if np.allclose(uav0.position, 0):
         print("   [WARNING] Pose toujours à (0,0,0) après 5 secondes. ")
         print("             -> Vérifiez que la simulation tourne (Clock/Bridge).")
         print("             -> Vérifiez le Topic: /uav_0/odometry")
    else:
         print(f"   [SUCCESS] Pose Reçue: {uav0.position}")
    # ---------------------------
    
    # Boucle de Test
    print("3. Boucle d'interaction (1000 steps)...")
    print("   [INFO] Monitoring: Affichage des détails (NFZ, Collisions, etc.) toutes les 10 steps.")

    for step in range(1000):
        # Actions Aléatoires (Remplacer par votre Agent RL ici)
        actions = {agent: env.action_space(agent).sample() for agent in env.agents}
        
        # Step
        observations, rewards, terminations, truncations, infos = env.step(actions)
        
        # Affichage
        if step % 10 == 0:
            print(f"--- Step {step} ---")
            for agent in env.agents:
                rew = rewards.get(agent, 0.0)
                info = infos.get(agent, {})
                breakdown = info.get("r_breakdown", {})
                
                # Format Breakdown string
                breakdown_str = " | ".join([f"{k}:{v:.1f}" for k, v in breakdown.items() if v != 0])
                
                print(f"   [{agent}] Total Reward: {rew:.2f}")
                if breakdown_str:
                    print(f"      -> Breakdown: {breakdown_str}")
                
                # Check for specific violations
                if info.get("collision", False):
                    print(f"      !!! CRASH DETECTED !!!")
                
                cost = info.get("cost", 0.0)
                if cost > 0:
                     print(f"      [VIOLATION] Cost: {cost} (NFZ/Boundary/Safety)")
        
        # Simulation d'un délai (pour voir ce qui se passe si on regarde la Simu)
        time.sleep(0.05) 

    # Sauvegarde de la Carte (Fonctionnalité IGN)
    print("4. Test de sauvegarde de la carte...")
    # Ensure directory exists in case CWD is weird
    output_path = "src/swarm_sim_pkg/swarm_sim/outputs/debug_map.npy"
    if not os.path.exists(os.path.dirname(output_path)):
         # Fallback to local outputs if path doesn't exist
         output_path = "outputs/debug_map.npy"
         
    env.save_occupancy_map(output_path)
    # Also save as LAZ for visualization
    laz_path = output_path.replace(".npy", ".laz")
    env.save_occupancy_map(laz_path)

    # 5. Save Global SLAM Map (MRG) - User Requirement: "GPS et tout ça"
    print("5. Sauvegarde des cartes Globales (SLAM MRG)...")
    import subprocess
    
    # Ensure outputs dir is absolute for ROS 2 service
    # If script running from root, abspath is cleaner
    abs_output_path = os.path.abspath("src/swarm_sim_pkg/swarm_sim/outputs")
    if not os.path.exists(abs_output_path):
        os.makedirs(abs_output_path, exist_ok=True)

    for i in range(3): # Hardcoded for 3 drones in debug
        agent = f"uav_{i}"
        filename = os.path.join(abs_output_path, f"slam_map_{agent}.pcd")
        
        # Service Call structure:
        # ros2 service call /uav_0/mrg_slam/save_map mrg_slam_msgs/srv/SaveMap "{file_path: ..., resolution: 0.1}"
        cmd = [
            "ros2", "service", "call",
            f"/{agent}/mrg_slam/save_map",
            "mrg_slam_msgs/srv/SaveMap",
            f"{{file_path: '{filename}', resolution: 0.1}}"
        ]
        
        print(f"   Requesting Map Save for {agent} -> {filename}...")
        try:
            # We use a timeout to avoid hanging if SLAM isn't running
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if "response" in result.stdout:
                print(f"   [SUCCESS] {agent} Map Saved.")
            else:
                 print(f"   [WARNING] Failed to save {agent} map. Is SLAM running? (ros2 launch swarm_sim swarm_slam.launch.py)")
                 # print(result.stderr)
        except subprocess.TimeoutExpired:
             print(f"   [TIMEOUT] Service call timed out for {agent}.")
        except Exception as e:
             print(f"   [ERROR] {e}")

    # Close
    env.close()
    print("=== Test Terminé avec Succès ===")

if __name__ == "__main__":
    main()
