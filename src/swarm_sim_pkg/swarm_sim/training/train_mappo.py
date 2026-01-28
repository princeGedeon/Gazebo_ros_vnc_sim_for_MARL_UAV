
import os
import ray
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.env.wrappers.pettingzoo_env import PettingZooEnv
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
    # 1. Register Env
    register_env("swarm_coverage", lambda config: PettingZooEnv(env_creator(config)))

    # 2. Config MAPPO
    # MAPPO = PPO with centralized critic. 
    # In RLLib, this is efficient via 'simple_optimizer' and sharing policies.
    
    config = (
        PPOConfig()
        .environment(
            "swarm_coverage", 
            env_config={
                "num_drones": 3,
                "nfz_config": "default" # Use 'default' (1 random zone) or pass list/int
            }
        )
        .framework("torch")
        .env_runners(num_env_runners=1, num_envs_per_env_runner=1)
        .training(
            model={"fcnet_hiddens": [256, 256]},
            lr=1e-4,
            gamma=0.99,
            lambda_=0.95,
            clip_param=0.2,
            entropy_coeff=0.01,
            # MAPPO Specifics can be tweaked here
            # For "Lagrangian", we would need custom callbacks or a specific algorithm
        )
        .multi_agent(
            # Parameter Sharing: All agents use "default_policy"
            policies={"shared_policy"},
            policy_mapping_fn=lambda agent_id, episode, worker, **kwargs: "shared_policy",
        )
        .resources(num_gpus=1)
    )

    print("Starting Ray RLLib (MAPPO) Training...")
    ray.init()
    
    tuner = tune.Tuner(
        "PPO",
        param_space=config.to_dict(),
        run_config=tune.RunConfig(
            stop={"training_iteration": 100},
            checkpoint_config=tune.CheckpointConfig(checkpoint_frequency=10),
            storage_path=os.path.abspath("./rllib_results")
        ),
    )
    
    results = tuner.fit()
    print("Training Completed.")
    ray.shutdown()

if __name__ == "__main__":
    train_mappo()
