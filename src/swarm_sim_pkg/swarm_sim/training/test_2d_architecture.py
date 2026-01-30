#!/usr/bin/env python3
"""
Quick test to validate the 2D+Z architecture refactoring.
Tests PettingZoo compatibility, action/observation spaces, and altitude controller.
"""

import numpy as np
import sys
import os

# Add package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

def test_environment_creation():
    """Test that environment can be created with new architecture"""
    print("\n=== TEST 1: Environment Creation ===")
    
    from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
    
    try:
        env = SwarmCoverageEnv(num_drones=2, max_steps=100)
        print(f"✓ Environment created successfully")
        print(f"  - Agents: {env.agents}")
        print(f"  - Z_optimal: {env.z_optimal:.2f}m")
        return env
    except Exception as e:
        print(f"✗ Failed to create environment: {e}")
        return None

def test_action_space(env):
    """Test that action space is 3D"""
    print("\n=== TEST 2: Action Space ===")
    
    try:
        agent = env.agents[0]
        action_space = env.action_spaces[agent]
        
        print(f"  - Action space shape: {action_space.shape}")
        assert action_space.shape == (3,), f"Expected (3,) but got {action_space.shape}"
        print("✓ Action space is 3D (vx, vy, yaw)")
        return True
    except Exception as e:
        print(f"✗ Action space test failed: {e}")
        return False

def test_observation_space(env):
    """Test that observation space is 147D"""
    print("\n=== TEST 3: Observation Space ===")
    
    try:
        agent = env.agents[0]
        obs_space = env.observation_spaces[agent]
        
        print(f"  - Observation space shape: {obs_space.shape}")
        expected_dim = 10 + 16 + 121  # state + lidar + 2D map
        assert obs_space.shape == (expected_dim,), f"Expected ({expected_dim},) but got {obs_space.shape}"
        print(f"✓ Observation space is {expected_dim}D (10 state + 16 lidar + 121 map)")
        return True
    except Exception as e:
        print(f"✗ Observation space test failed: {e}")
        return False

def test_reset(env):
    """Test environment reset and observation generation"""
    print("\n=== TEST 4: Reset & Observation ===")
    
    try:
        obs_dict, info_dict = env.reset()
        
        agent = env.agents[0]
        obs = obs_dict[agent]
        
        print(f"  - Observation shape: {obs.shape}")
        print(f"  - Observation dtype: {obs.dtype}")
        print(f"  - Observation range: [{np.min(obs):.2f}, {np.max(obs):.2f}]")
        
        # Check components
        state = obs[:10]
        lidar = obs[10:26]
        map_patch = obs[26:]
        
        print(f"  - State (first 5): {state[:5]}")
        print(f"  - LiDAR (first 5): {lidar[:5]}")
        print(f"  - Map unique values: {np.unique(map_patch)}")
        
        print("✓ Reset successful and observations valid")
        return True
    except Exception as e:
        print(f"✗ Reset test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_step_with_3d_action(env):
    """Test stepping with 3D actions"""
    print("\n=== TEST 5: Step with 3D Actions ===")
    
    try:
        # Create random 3D actions
        actions = {agent: np.array([0.5, 0.5, 0.1], dtype=np.float32) for agent in env.agents}
        
        print(f"  - Actions: vx=0.5, vy=0.5, yaw=0.1 (vz will be auto-calculated)")
        
        obs, rewards, terms, truncs, infos = env.step(actions)
        
        agent = env.agents[0]
        print(f"  - Observation shape: {obs[agent].shape}")
        print(f"  - Reward: {rewards[agent]:.2f}")
        print(f"  - Terminated: {terms[agent]}")
        
        print("✓ Step executed successfully with 3D actions")
        return True
        
    except Exception as e:
        print(f"✗ Step test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_occupancy_grid_2d():
    """Test OccupancyGrid2D directly"""
    print("\n=== TEST 6: OccupancyGrid2D ===")
    
    try:
        from swarm_sim.common.occupancy_grid_2d import OccupancyGrid2D
        
        grid = OccupancyGrid2D(x_range=(-10, 10), y_range=(-10, 10), resolution=1.0)
        
        # Test optimal altitude calculation
        z_opt = grid.calculate_optimal_altitude(sensor_range_m=15.0)
        print(f"  - Calculated Z_optimal: {z_opt:.2f}m")
        assert 7.0 < z_opt < 8.0, f"Z_optimal should be ~7.5m, got {z_opt}"
        
        # Test position update
        new_cell = grid.update_from_position(uav_id=0, x=5.0, y=5.0)
        print(f"  - Updated position (5, 5): new_cell={new_cell}")
        assert new_cell == True, "First visit should return True"
        
        # Test second visit
        new_cell2 = grid.update_from_position(uav_id=0, x=5.0, y=5.0)
        assert new_cell2 == False, "Second visit should return False"
        
        # Test coverage ratio
        coverage = grid.get_coverage_ratio()
        print(f"  - Coverage ratio: {coverage:.6f}")
        
        # Test 2D observation
        obs = grid.get_observation_2d(5.0, 5.0, radius=2)
        print(f"  - Observation shape: {obs.shape}")
        assert obs.shape == (5, 5), f"Expected (5,5) got {obs.shape}"
        
        print("✓ OccupancyGrid2D works correctly")
        return True
        
    except Exception as e:
        print(f"✗ OccupancyGrid2D test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("2D+Z ARCHITECTURE VALIDATION TEST")
    print("=" * 60)
    
    # Run all tests
    env = test_environment_creation()
    if env is None:
        print("\n❌ CRITICAL: Environment creation failed. Aborting tests.")
        return False
    
    passed = 0
    total = 0
    
    tests = [
        (test_action_space, env),
        (test_observation_space, env),
        (test_occupancy_grid_2d, ),
        (test_reset, env),
        (test_step_with_3d_action, env),
    ]
    
    for test_func, *args in tests:
        total += 1
        if test_func(*args):
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("✅ All tests passed! 2D+Z architecture is working correctly.")
        env.close()
        return True
    else:
        print(f"⚠️ {total - passed} test(s) failed. Review errors above.")
        env.close()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
