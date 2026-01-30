
import os
import ray
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.env.wrappers.pettingzoo_env import ParallelPettingZooEnv
from ray.tune.registry import register_env
from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv

def env_creator(config):
    # Retrieve config from the 'config' dict if passed by RLLib
    num_drones = config.get("num_drones", 3)
    nfz_config = config.get("nfz_config", 'default') # Can be 'default', int, or list
    
    env = SwarmCoverageEnv(
        num_drones=num_drones,
        nfz_config=nfz_config,
        min_height=2.0,
        max_height=10.0,
        max_steps=500 # Shorter episodes to learn faster initially
    )
    return env

def train_mappo():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100, help="Number of training iterations (epochs)")
    parser.add_argument("--max-steps", type=int, default=500, help="Max steps per episode")
    parser.add_argument("--num-drones", type=int, default=3, help="Number of drones")
    parser.add_argument("--algo", type=str, default="simple", choices=["simple", "lagrangian", "cbf"], help="Algorithm capability")
    # Added to match autolaunch script
    parser.add_argument("--total-timesteps", type=int, default=500000, help="Total training timesteps")
    parser.add_argument("--checkpoint-freq", type=int, default=10, help="Checkpoint frequency (iterations)")
    parser.add_argument("--output-dir", type=str, default="./rllib_results", help="Output directory")
    args = parser.parse_args()

    # 1. Register Env
    # Pass args via lambda closure (Simpler than full config passing for EnvCreator)
    # Note: changes to env_creator signature would be better but this works for closure.
    def env_creator_wrapper(config):
        config["num_drones"] = args.num_drones
        config["max_steps"] = args.max_steps # Pass custom steps
        
        # Case 3: CBF
        if args.algo == "cbf":
            config["use_cbf"] = True
        else:
            config["use_cbf"] = False
            
        return env_creator(config)

    register_env("swarm_coverage", lambda config: ParallelPettingZooEnv(env_creator_wrapper(config)))

    # 2. Config MAPPO
    exp_name = f"MAPPO_{args.algo.upper()}"
    
    config = (
        PPOConfig()
        .environment(
            "swarm_coverage", 
            env_config={
                "num_drones": args.num_drones,
                "nfz_config": "default",
                "use_cbf": (args.algo == "cbf")
            }
        )
        .framework("torch")
        .env_runners(num_env_runners=1, num_envs_per_env_runner=1)
        .training(
            model={"fcnet_hiddens": [256, 256]},
            lr=1e-4, # Standard Learning Rate
            gamma=0.99,
            lambda_=0.95,
            clip_param=0.2,
            entropy_coeff=0.01,
            train_batch_size=4000, # Explicit default
        )
        .multi_agent(
            # Parameter Sharing: All agents use "default_policy"
            policies={"shared_policy"},
            policy_mapping_fn=lambda agent_id, *args, **kwargs: "shared_policy",
        )
        .resources(num_gpus=1)
        # Disable new API stack for now to avoid warnings/errors with custom models
        .api_stack(enable_rl_module_and_learner=False, enable_env_runner_and_connector_v2=False)
    )

    print(f"Starting Ray RLLib (MAPPO) Training...")
    print(f"Hyperparams: Iterations={args.iterations}, Steps/Ep={args.max_steps}, Drones={args.num_drones}")
    # Init Ray with Dashboard exposed
    ray.init(dashboard_host="0.0.0.0", include_dashboard=True, ignore_reinit_error=True)
    
    tuner = tune.Tuner(
        "PPO",
        param_space=config.to_dict(),
        run_config=tune.RunConfig(
            stop={"timesteps_total": args.total_timesteps} if args.total_timesteps > 0 else {"training_iteration": args.iterations},
            checkpoint_config=tune.CheckpointConfig(checkpoint_frequency=args.checkpoint_freq),
            storage_path=os.path.abspath(args.output_dir)
        ),
    )
    
    results = tuner.fit()
    print("Training Completed.")
    ray.shutdown()

if __name__ == "__main__":
    train_mappo()
