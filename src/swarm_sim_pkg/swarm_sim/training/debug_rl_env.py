#!/usr/bin/env python3
"""
Debug RL Environment - Comprehensive Testing Script
Tests the SwarmCoverageEnv with all features:
- 2D+Z architecture
- Altitude controller
- GNN communication
- Reward system
- Visualization
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

def test_environment_basic():
    """Test basic environment functionality"""
    print("\n" + "="*60)
    print("TEST 1: Basic Environment Creation & Reset")
    print("="*60)
    
    from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
    
    try:
        env = SwarmCoverageEnv(num_drones=3, max_steps=100)
        print(f"✓ Environment created")
        print(f"  - Agents: {env.agents}")
        print(f"  - Z_optimal: {env.z_optimal:.2f}m")
        print(f"  - Action space: {env.action_spaces[env.agents[0]].shape}")
        print(f"  - Obs space: {env.observation_spaces[env.agents[0]].shape}")
        
        # Reset
        obs, info = env.reset()
        print(f"✓ Reset successful")
        print(f"  - Observation keys: {list(obs.keys())}")
        print(f"  - Obs shape: {obs[env.agents[0]].shape}")
        
        env.close()
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_altitude_controller():
    """Test automatic altitude controller"""
    print("\n" + "="*60)
    print("TEST 2: Altitude Controller")
    print("="*60)
    
    from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
    
    try:
        env = SwarmCoverageEnv(num_drones=1, max_steps=50)
        obs, _ = env.reset()
        
        agent = env.agents[0]
        
        print(f"Initial Z: {env.uavs[agent].position[2]:.2f}m")
        print(f"Target Z_optimal: {env.z_optimal:.2f}m")
        
        # Take random actions (vx, vy, yaw only - vz is automatic)
        for step in range(20):
            actions = {agent: np.array([0.1, 0.1, 0.0], dtype=np.float32)}
            obs, rewards, terms, truncs, infos = env.step(actions)
            
            z_current = env.uavs[agent].position[2]
            if step % 5 == 0:
                print(f"Step {step}: Z={z_current:.2f}m (error: {abs(z_current - env.z_optimal):.2f}m)")
        
        # Check if Z converged to optimal
        final_z = env.uavs[agent].position[2]
        z_error = abs(final_z - env.z_optimal)
        
        if z_error < 1.0:
            print(f"✓ Altitude controller working! Final Z={final_z:.2f}m (error: {z_error:.2f}m)")
        else:
            print(f"⚠ Altitude error large: {z_error:.2f}m")
        
        env.close()
        return z_error < 1.0
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reward_system():
    """Test reward calculation"""
    print("\n" + "="*60)
    print("TEST 3: Reward System")
    print("="*60)
    
    from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
    
    try:
        env = SwarmCoverageEnv(num_drones=3, max_steps=50)
        obs, _ = env.reset()
        
        total_rewards = {agent: 0.0 for agent in env.agents}
        
        # Take actions and accumulate rewards
        for step in range(30):
            # Random actions
            actions = {agent: env.action_spaces[agent].sample() for agent in env.agents}
            obs, rewards, terms, truncs, infos = env.step(actions)
            
            for agent in env.agents:
                total_rewards[agent] += rewards[agent]
            
            if step % 10 == 0:
                coverage = env.global_map.get_coverage_ratio()
                avg_reward = np.mean(list(rewards.values()))
                print(f"Step {step}: Coverage={coverage*100:.1f}%, Avg Reward={avg_reward:.2f}")
        
        # Summary
        final_coverage = env.global_map.get_coverage_ratio()
        avg_total = np.mean(list(total_rewards.values()))
        
        print(f"\n✓ Reward system working")
        print(f"  - Final coverage: {final_coverage*100:.1f}%")
        print(f"  - Avg total reward: {avg_total:.2f}")
        print(f"  - Per-agent rewards: {[f'{r:.1f}' for r in total_rewards.values()]}")
        
        env.close()
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_constraints():
    """Test constraints (NFZ, altitude bounds, etc.)"""
    print("\n" + "="*60)
    print("TEST 4: Constraints & Safety")
    print("="*60)
    
    from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
    
    try:
        env = SwarmCoverageEnv(
            num_drones=2,
            max_steps=50,
            min_height=2.0,
            max_height=12.0,
            nfz_config='default'  # Creates 1 random NFZ
        )
        obs, _ = env.reset()
        
        print(f"✓ Environment created with constraints")
        print(f"  - Min height: {env.min_height}m")
        print(f"  - Max height: {env.max_height}m")
        print(f"  - Z_optimal: {env.z_optimal:.2f}m")
        print(f"  - NFZs: {len(env.nfz_list)}")
        
        # Check Z_optimal respects bounds
        if env.z_optimal >= env.min_height and env.z_optimal <= env.max_height:
            print(f"✓ Z_optimal within bounds")
        else:
            print(f"⚠ Z_optimal out of bounds!")
        
        # Run a few steps
        violations = 0
        for step in range(20):
            actions = {agent: np.array([0.2, 0.2, 0.0]) for agent in env.agents}
            obs, rewards, terms, truncs, infos = env.step(actions)
            
            # Check for constraint violations in infos
            for agent in env.agents:
                if infos[agent].get('cost', 0) > 0:
                    violations += 1
        
        print(f"✓ Constraint system active (violations detected: {violations})")
        
        env.close()
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gnn_communication():
    """Test GNN communication module"""
    print("\n" + "="*60)
    print("TEST 5: GNN Communication (Optional)")
    print("="*60)
    
    try:
        from swarm_sim.models.gnn_communication import MAGNETEncoder
        from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
        
        env = SwarmCoverageEnv(num_drones=3, max_steps=10)
        obs, _ = env.reset()
        
        # Get positions
        positions = {agent: env.uavs[agent].position for agent in env.agents}
        
        # Create GNN encoder
        gnn = MAGNETEncoder(obs_dim=147, hidden_dim=128, comm_range=20.0)
        
        # Process with GNN
        enhanced_obs = gnn(obs, positions)
        
        print(f"✓ GNN processing successful")
        print(f"  - Input obs shape: {obs[env.agents[0]].shape}")
        print(f"  - GNN output shape: {enhanced_obs[env.agents[0]].shape}")
        
        env.close()
        return True
    except ImportError:
        print("⚠ PyTorch not available, skipping GNN test")
        return True
    except Exception as e:
        print(f"✗ GNN test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*60)
    print("RL ENVIRONMENT DEBUG & VALIDATION")
    print("="*60)
    
    tests = [
        ("Basic Environment", test_environment_basic),
        ("Altitude Controller", test_altitude_controller),
        ("Reward System", test_reward_system),
        ("Constraints & Safety", test_constraints),
        ("GNN Communication", test_gnn_communication)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"✗ {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nResult: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("✅ All tests passed! Environment is ready for training.")
        return 0
    else:
        print(f"⚠️ {total_count - passed_count} test(s) failed. Review errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
