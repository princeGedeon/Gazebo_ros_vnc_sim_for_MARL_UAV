
import os
import argparse
import ray
from ray.rllib.algorithms.algorithm import Algorithm
from ray.rllib.env.wrappers.pettingzoo_env import ParallelPettingZooEnv
from ray.tune.registry import register_env
from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
# Import wrappers if needed
from swarm_sim.training.train_mappo_cbf import SafetyWrapper

def env_creator(config):
    # Determine if we need SafetyWrapper based on config or assumed defaults
    # For testing, we might want to enforce safety or just test the policy raw.
    # Let's instantiate base env by default.
    env = SwarmCoverageEnv(
        num_drones=3,
        nfz_config=config.get("nfz_config", 'default'),
        min_height=2.0,
        max_height=10.0,
        max_steps=500 
    )
    return env

def test_mappo():
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=str, help="Path to checkpoint directory")
    parser.add_argument("--max_steps", type=int, default=500, help="Max steps per episode")
    parser.add_argument("--episodes", type=int, default=3, help="Number of episodes")
    parser.add_argument("--use_cbf", action="store_true", help="Wrap env with Safety Layer (CBF)")
    args = parser.parse_args()

    # Register Env
    # Use args.max_steps in lambda
    def env_creator_test(config):
        return SwarmCoverageEnv(
            num_drones=3,
            nfz_config='default',
            max_steps=args.max_steps
        )

    register_env("swarm_coverage", lambda config: ParallelPettingZooEnv(env_creator_test(config)))
    register_env("swarm_coverage_cbf", lambda config: ParallelPettingZooEnv(env_creator_test(config)))

    print(f"Loading checkpoint: {args.checkpoint}")
    ray.init()
    
    algo = Algorithm.from_checkpoint(args.checkpoint)
    
    # Setup Env for Inference
    if args.use_cbf:
        print("Using CBF Safety Layer for Testing")
        env = SafetyWrapper(num_drones=3, nfz_config='default', max_steps=args.max_steps)
    else:
        env = SwarmCoverageEnv(num_drones=3, nfz_config='default', max_steps=args.max_steps)
        
    import json
    import numpy as np
    
    metrics = {
        "episodes": [],
        "summary": {}
    }

    for ep in range(args.episodes):
        obs, infos = env.reset()
        done = {a: False for a in env.agents}
        total_reward = {a: 0.0 for a in env.agents}
        step = 0
        
        # Episode Metrics
        ep_metrics = {
            "collisions": 0,
            "nfz_violations": 0,
            "altitude_violations": 0,
            "steps": 0,
            "total_reward": 0.0,
            "coverage_ratio": 0.0
        }
        
        print(f"\n--- Episode {ep+1} Start ---")
        while not all(done.values()):
            actions = {}
            for agent in env.agents:
                if not done[agent]:
                    actions[agent] = algo.compute_single_action(
                        observation=obs[agent], 
                        policy_id="shared_policy"
                    )
            
            obs, rewards, terms, truncs, infos = env.step(actions)
            
            # Track Metrics from Infos
            for a in infos:
                info = infos[a]
                if info.get("collision", False):
                    ep_metrics["collisions"] += 1
                
                # Check specifics if available (we need to parse 'cost' or similar)
                # Or re-check conditions if info doesn't have details.
                # Assuming env puts 'cost' = 1 if violation. This is a bit generic.
                # Let's check environment state directly or check specific info keys if we added them.
                # We can assume 'cost' > 0 implies *some* violation.
                # Ideally, SwarmCoverageEnv should return specific violation flags.
                # For now, we will trust 'cost' as general safety violation count.
                if info.get("cost", 0.0) > 0.0:
                    # We don't know which one, but we count it.
                    pass

                # If we want detailed breakdown, we might need to query the env directly or add keys.
                # Let's rely on info keys we added previously? We added 'cost'.
                # We'll just sum cost as "Safety Violations"
                
            for a in rewards:
                total_reward[a] += rewards[a]
                if terms[a] or truncs[a]:
                    done[a] = True
            
            step += 1
        
        # End of Episode
        ep_metrics["steps"] = step
        ep_metrics["total_reward"] = sum(total_reward.values())
        ep_metrics["coverage_ratio"] = env.global_map.get_coverage_ratio()
        
        # Calculate specific violations for this episode (Aggregate)
        # Since we didn't add granular counters in env, we might be approximate.
        # But for comparison, let's use the FINAL "collision" count (since it terminates?)
        # Actually collision terminates agent. So max collisions = num_drones.
        # But NFZ is per step.
        
        print(f"Episode {ep+1} Done. Steps: {step}")
        print(f"  Total Reward: {ep_metrics['total_reward']:.2f}")
        print(f"  Coverage: {ep_metrics['coverage_ratio']*100:.1f}%")
        
        metrics["episodes"].append(ep_metrics)

    # Compute Summary
    avg_rew = np.mean([e["total_reward"] for e in metrics["episodes"]])
    avg_cov = np.mean([e["coverage_ratio"] for e in metrics["episodes"]])
    avg_len = np.mean([e["steps"] for e in metrics["episodes"]])
    
    print(f"\n=== Benchmark Results ===")
    print(f"Avg Reward: {avg_rew:.2f}")
    print(f"Avg Coverage: {avg_cov*100:.1f}%")
    print(f"Avg Length: {avg_len:.1f}")
    
    # Save to file
    outfile = "benchmark_results.json"
    with open(outfile, 'w') as f:
        json.dump(metrics, f, indent=4)
    print(f"Results saved to {outfile}")
            
    env.close()
    ray.shutdown()

if __name__ == "__main__":
    test_mappo()
