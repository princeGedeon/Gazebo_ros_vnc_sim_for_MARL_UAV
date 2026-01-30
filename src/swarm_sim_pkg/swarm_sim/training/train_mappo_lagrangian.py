
import os
import ray
import numpy as np
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.algorithms.callbacks import DefaultCallbacks
from ray.rllib.env.wrappers.pettingzoo_env import ParallelPettingZooEnv
from ray.tune.registry import register_env
from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv

# Global Lagrange Multiplier (Simple Shared State)
# In a distributed setup, this should be an Actor, but for single-node simulation, this works.
class LagrangeMultiplier:
    def __init__(self, cost_limit=0.1, lr=0.01, init_lambda=1.0):
        self.cost_limit = cost_limit
        self.lr = lr
        self.param = init_lambda
        self.avg_cost = 0.0

    def update(self, current_cost):
        # Dual Ascent: lambda = lambda + lr * (cost - limit)
        # If cost > limit, lambda increases (more penalty).
        # If cost < limit, lambda decreases.
        diff = current_cost - self.cost_limit
        self.param += self.lr * diff
        self.param = max(0.0, self.param)
        self.avg_cost = current_cost
        return self.param

# Singleton instance
LAGRANGE = LagrangeMultiplier(cost_limit=0.05, lr=0.05, init_lambda=5.0)

class LagrangianCallbacks(DefaultCallbacks):
    def on_postprocess_trajectory(
        self,
        *,
        worker,
        episode,
        agent_id,
        policy_id,
        policies,
        postprocessed_batch,
        original_batches,
        **kwargs
    ):
        """
        Modify rewards in the batch: R_prime = R_objective - lambda * Cost
        """
        if "infos" not in postprocessed_batch:
            return

        # Extract costs from infos. 
        # Note: infos in postprocessed_batch is a list of dicts or a structured array
        infos = postprocessed_batch["infos"]
        rewards = postprocessed_batch["rewards"]
        
        # We need to parse costs. RLLib efficiently stores infos.
        # If it's a list:
        costs = []
        for info in infos:
            c = info.get("cost", 0.0) if isinstance(info, dict) else 0.0
            costs.append(c)
        
        costs = np.array(costs)
        
        # Apply Penalty
        # lambda is global
        penalty = LAGRANGE.param * costs
        
        # Modify rewards in-place
        postprocessed_batch["rewards"] = rewards - penalty
        
        # Store cost for metrics
        episode.custom_metrics[f"cost_{agent_id}"] = np.sum(costs)
        episode.custom_metrics[f"lambda"] = LAGRANGE.param

    def on_train_result(self, *, algorithm, result, **kwargs):
        """
        Update Lambda at the end of each iteration based on average cost
        """
        # Get average cost from custom metrics
        # RLLib aggregates custom_metrics automatically
        if "custom_metrics" in result and "cost_uav_0_mean" in result["custom_metrics"]:
            # Aggregate all agents costs
            total_cost = 0
            count = 0
            for key, val in result["custom_metrics"].items():
                if "cost_uav" in key and "_mean" in key:
                    total_cost += val
                    count += 1
            
            avg_cost = total_cost / max(1, count)
            
            # Since cost is "sum per episode", and limit is "rate"? 
            # Ideally limit is "Expected Cumulative Cost" or "Cost Rate".
            # If cost=1 per step, sum=500. Limit=25 (5% violation).
            # Let's assume Limit is defined as Episode Sum Limit.
            # My LAGRANGE init uses 0.05 which implies rate? 
            # Let's adjust LAGRANGE to use Expected Sum Limit.
            # If we want < 5% violation steps: 500 steps * 0.05 = 25.
            
            # Re-configure global if needed, but let's assume we use the param:
            # We want to normalize or match the scale.
            # Let's use Normalized Cost (0-1) per step? No, RLLib gives Episode Sum.
            
            # Let's normalize by episode length approx (500)
            avg_cost_rate = avg_cost / 500.0
            
            new_lambda = LAGRANGE.update(avg_cost_rate)
            
            print(f"\n[Lagrangian] Iteration Report:")
            print(f"  Avg Cost Rate: {avg_cost_rate:.4f} (Limit: {LAGRANGE.cost_limit})")
            print(f"  New Lambda: {new_lambda:.4f}")
            
            # Log to result for Tensorboard
            result["custom_metrics"]["lambda"] = new_lambda
            result["custom_metrics"]["cost_rate"] = avg_cost_rate

def env_creator(config):
    env = SwarmCoverageEnv(
        num_drones=3,
        nfz_config=config.get("nfz_config", 'default'),
        min_height=2.0,
        max_height=10.0,
        max_steps=500 
    )
    return env

def train_lagrangian():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100, help="Number of training iterations (epochs)")
    parser.add_argument("--max-steps", type=int, default=500, help="Max steps per episode")
    parser.add_argument("--num-drones", type=int, default=3, help="Number of drones")
    # Added to match autolaunch script
    parser.add_argument("--total-timesteps", type=int, default=500000, help="Total training timesteps")
    parser.add_argument("--checkpoint-freq", type=int, default=10, help="Checkpoint frequency (iterations)")
    parser.add_argument("--output-dir", type=str, default="./rllib_results", help="Output directory")
    args = parser.parse_args()

    # Wrapper to inject args
    def env_creator_wrapper(config):
        config["num_drones"] = args.num_drones
        config["max_steps"] = args.max_steps
        return env_creator(config)

    register_env("swarm_coverage", lambda config: ParallelPettingZooEnv(env_creator_wrapper(config)))

    config = (
        PPOConfig()
        .environment(
            "swarm_coverage", 
            env_config={
                "num_drones": args.num_drones,
                "nfz_config": "default"
            }
        )
        .framework("torch")
        .callbacks(LagrangianCallbacks)
        .env_runners(num_env_runners=1, num_envs_per_env_runner=1)
        .training(
            model={"fcnet_hiddens": [256, 256]},
            lr=1e-4, 
            gamma=0.99,
            train_batch_size=4000,
        )
        .multi_agent(
            policies={"shared_policy"},
            policy_mapping_fn=lambda agent_id, *args, **kwargs: "shared_policy",
        )
        .resources(num_gpus=1)
        .api_stack(enable_rl_module_and_learner=False, enable_env_runner_and_connector_v2=False)
    )

    print(f"Starting Lagrangian MAPPO Training...")
    print(f"Hyperparams: Iterations={args.iterations}, Steps/Ep={args.max_steps}, Drones={args.num_drones}")
    
    # Init Ray with Dashboard exposed
    ray.init(dashboard_host="0.0.0.0", include_dashboard=True, ignore_reinit_error=True)
    
    # Estimate Time:
    # 100 Iterations. 
    # 1 Iteration ~ 4000 steps.
    # Sim Speed ~ 100 steps/sec (optimistic) -> 40s/iter.
    # Total ~ 100 * 40s = 4000s (~1.1 hours).
    print("Estimated Duration: ~1-2 Hours (depending on Sim Speed)")
    
    tuner = tune.Tuner(
        "PPO",
        param_space=config.to_dict(),
        run_config=tune.RunConfig(
        run_config=tune.RunConfig(
            name="mappo_lagrangian",
            stop={"timesteps_total": args.total_timesteps} if args.total_timesteps > 0 else {"training_iteration": args.iterations},
            checkpoint_config=tune.CheckpointConfig(checkpoint_frequency=args.checkpoint_freq),
            storage_path=os.path.abspath(args.output_dir)
        ),
    )
    
    tuner.fit()
    print("Lagrangian Training Completed.")

if __name__ == "__main__":
    train_lagrangian()
