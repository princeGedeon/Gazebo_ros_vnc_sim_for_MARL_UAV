#!/usr/bin/env python3
"""
Comprehensive Test Script for RL Environment
- Random Baseline: Evaluate untrained random policy
- Trained Evaluation: Load checkpoint and evaluate
- Comparison: Generate performance graphs
"""

import numpy as np
import sys
import os
import matplotlib.pyplot as plt
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

def run_random_baseline(num_episodes=50, max_steps=500):
    """
    Run random actions to establish baseline performance.
    
    Returns:
        stats: Dict with episode_returns, coverage_ratios, battery_usage
    """
    print("\n" + "="*60)
    print("RANDOM BASELINE EVALUATION")
    print("="*60)
    
    from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
    
    env = SwarmCoverageEnv(num_drones=3, max_steps=max_steps)
    
    episode_returns = []
    coverage_ratios = []
    battery_usage = []
    
    for ep in range(num_episodes):
        obs, info = env.reset()
        episode_return = {agent: 0.0 for agent in env.agents}
        done = False
        step = 0
        
        while step < max_steps and not done:
            # Random actions
            actions = {agent: env.action_spaces[agent].sample() for agent in env.agents}
            
            obs, rewards, terms, truncs, infos = env.step(actions)
            
            for agent in env.agents:
                episode_return[agent] += rewards[agent]
            
            done = all(terms.values()) or all(truncs.values())
            step += 1
        
        # Collect stats
        avg_return = np.mean(list(episode_return.values()))
        coverage = env.global_map.get_coverage_ratio()
        avg_battery = np.mean([env.uavs[a].battery.get_percentage() for a in env.agents])
        
        episode_returns.append(avg_return)
        coverage_ratios.append(coverage)
        battery_usage.append(100 - avg_battery)
        
        if (ep + 1) % 10 == 0:
            print(f"Episode {ep+1}/{num_episodes}: Return={avg_return:.1f}, Coverage={coverage*100:.1f}%, Battery Used={100-avg_battery:.1f}%")
    
    env.close()
    
    stats = {
        'episode_returns': episode_returns,
        'coverage_ratios': coverage_ratios,
        'battery_usage': battery_usage,
        'mean_return': np.mean(episode_returns),
        'mean_coverage': np.mean(coverage_ratios),
        'mean_battery': np.mean(battery_usage)
    }
    
    print(f"\n📊 RANDOM BASELINE RESULTS:")
    print(f"  - Mean Return: {stats['mean_return']:.2f}")
    print(f"  - Mean Coverage: {stats['mean_coverage']*100:.2f}%")
    print(f"  - Mean Battery Used: {stats['mean_battery']:.2f}%")
    
    return stats

def run_trained_evaluation(checkpoint_path, num_episodes=50, max_steps=500):
    """
    Evaluate trained policy from checkpoint.
    
    Args:
        checkpoint_path: Path to trained model checkpoint
    
    Returns:
        stats: Same format as random baseline
    """
    print("\n" + "="*60)
    print("TRAINED POLICY EVALUATION")
    print("="*60)
    
    if not os.path.exists(checkpoint_path):
        print(f"❌ Checkpoint not found: {checkpoint_path}")
        print("   Train a model first using: ./scripts/autolaunch_case_1.sh")
        return None
    
    from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
    
    # Try importing Ray/RLlib for policy loading
    try:
        from ray.rllib.algorithms.ppo import PPO
        import ray
        
        ray.init(ignore_reinit_error=True)
        
        # Load trained agent
        agent = PPO.from_checkpoint(checkpoint_path)
        print(f"✓ Loaded checkpoint: {checkpoint_path}")
        
    except ImportError:
        print("❌ Ray/RLlib not available. Cannot load trained policy.")
        return None
    
    env = SwarmCoverageEnv(num_drones=3, max_steps=max_steps)
    
    episode_returns = []
    coverage_ratios = []
    battery_usage = []
    
    for ep in range(num_episodes):
        obs, info = env.reset()
        episode_return = {agent: 0.0 for agent in env.agents}
        done = False
        step = 0
        
        while step < max_steps and not done:
            # Trained actions
            actions = {}
            for agent in env.agents:
                action = agent.compute_single_action(obs[agent])
                actions[agent] = action
            
            obs, rewards, terms, truncs, infos = env.step(actions)
            
            for agent in env.agents:
                episode_return[agent] += rewards[agent]
            
            done = all(terms.values()) or all(truncs.values())
            step += 1
        
        # Collect stats
        avg_return = np.mean(list(episode_return.values()))
        coverage = env.global_map.get_coverage_ratio()
        avg_battery = np.mean([env.uavs[a].battery.get_percentage() for a in env.agents])
        
        episode_returns.append(avg_return)
        coverage_ratios.append(coverage)
        battery_usage.append(100 - avg_battery)
        
        if (ep + 1) % 10 == 0:
            print(f"Episode {ep+1}/{num_episodes}: Return={avg_return:.1f}, Coverage={coverage*100:.1f}%, Battery Used={100-avg_battery:.1f}%")
    
    env.close()
    ray.shutdown()
    
    stats = {
        'episode_returns': episode_returns,
        'coverage_ratios': coverage_ratios,
        'battery_usage': battery_usage,
        'mean_return': np.mean(episode_returns),
        'mean_coverage': np.mean(coverage_ratios),
        'mean_battery': np.mean(battery_usage)
    }
    
    print(f"\n📊 TRAINED POLICY RESULTS:")
    print(f"  - Mean Return: {stats['mean_return']:.2f}")
    print(f"  - Mean Coverage: {stats['mean_coverage']*100:.2f}%")
    print(f"  - Mean Battery Used: {stats['mean_battery']:.2f}%")
    
    return stats

def plot_comparison(random_stats, trained_stats, output_dir="outputs/eval"):
    """Generate comparison plots"""
    os.makedirs(output_dir, exist_ok=True)
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    # Returns
    axes[0].hist(random_stats['episode_returns'], alpha=0.5, label='Random', bins=20, color='red')
    if trained_stats:
        axes[0].hist(trained_stats['episode_returns'], alpha=0.5, label='Trained', bins=20, color='green')
    axes[0].set_xlabel('Episode Return')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title('Episode Returns')
    axes[0].legend()
    
    # Coverage
    axes[1].hist([c*100 for c in random_stats['coverage_ratios']], alpha=0.5, label='Random', bins=20, color='red')
    if trained_stats:
        axes[1].hist([c*100 for c in trained_stats['coverage_ratios']], alpha=0.5, label='Trained', bins=20, color='green')
    axes[1].set_xlabel('Coverage (%)')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title('Coverage Ratios')
    axes[1].legend()
    
    # Battery
    axes[2].hist(random_stats['battery_usage'], alpha=0.5, label='Random', bins=20, color='red')
    if trained_stats:
        axes[2].hist(trained_stats['battery_usage'], alpha=0.5, label='Trained', bins=20, color='green')
    axes[2].set_xlabel('Battery Used (%)')
    axes[2].set_ylabel('Frequency')
    axes[2].set_title('Battery Usage')
    axes[2].legend()
    
    plt.tight_layout()
    
    filename = f"{output_dir}/comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150)
    print(f"\n📊 Comparison plot saved: {filename}")
    plt.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate RL policies")
    parser.add_argument('--mode', choices=['random', 'trained', 'both'], default='random',
                       help='Evaluation mode')
    parser.add_argument('--checkpoint', type=str, default=None,
                       help='Path to trained checkpoint')
    parser.add_argument('--episodes', type=int, default=50,
                       help='Number of evaluation episodes')
    parser.add_argument('--max-steps', type=int, default=500,
                       help='Max steps per episode')
    
    args = parser.parse_args()
    
    random_stats = None
    trained_stats = None
    
    if args.mode in ['random', 'both']:
        random_stats = run_random_baseline(args.episodes, args.max_steps)
    
    if args.mode in ['trained', 'both']:
        if args.checkpoint is None:
            print("❌ --checkpoint required for trained evaluation")
            sys.exit(1)
        trained_stats = run_trained_evaluation(args.checkpoint, args.episodes, args.max_steps)
    
    if random_stats and trained_stats:
        plot_comparison(random_stats, trained_stats)
        
        # Print improvement
        print("\n" + "="*60)
        print("IMPROVEMENT SUMMARY")
        print("="*60)
        return_improve = ((trained_stats['mean_return'] - random_stats['mean_return']) / abs(random_stats['mean_return'])) * 100
        coverage_improve = ((trained_stats['mean_coverage'] - random_stats['mean_coverage']) / random_stats['mean_coverage']) * 100
        
        print(f"Return:   {random_stats['mean_return']:.1f} → {trained_stats['mean_return']:.1f} ({return_improve:+.1f}%)")
        print(f"Coverage: {random_stats['mean_coverage']*100:.1f}% → {trained_stats['mean_coverage']*100:.1f}% ({coverage_improve:+.1f}%)")

if __name__ == "__main__":
    main()
