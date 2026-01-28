
# train_benchmarl.py
# BenchMARL Integration for Swarm Coverage
# Req: pip install benchmarl torchrl

import torch
from benchmarl.algorithms import IppoConfig
from benchmarl.environments import PettingZooTask
from benchmarl.experiment import Experiment, ExperimentConfig
from benchmarl.models.mlp import MlpConfig

from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv

def train_benchmarl():
    print("Initializing BenchMARL Experiment...")
    
    # 1. Define Task from PettingZoo Env
    # BenchMARL expects a lambda that returns the env
    task = PettingZooTask(
        lambda: SwarmCoverageEnv(
            num_drones=3,
            nfz_config='default', # Use new features
            max_steps=500
        ),
        "swarm_coverage_v0"
    )

    # 2. Algorithm Config (IPPO - Independent PPO)
    algorithm_config = IppoConfig(
        share_param_critic=True,
        clip_epsilon=0.2,
        entropy_coef=0.01,
        critic_loss_coef=1.0,
        loss_critic_type="l2",
        lr=3e-4,
        gamma=0.99,
        lmbda=0.9
    )

    # 3. Model Config (MLP Policy)
    model_config = MlpConfig(
        num_cells=[256, 256],
        activation_class=torch.nn.Tanh
    )

    # 4. Experiment Config
    experiment_config = ExperimentConfig(
        max_n_frames=1_000_000,   # Total frames
        on_policy_collected_frames_per_batch=6000,
        on_policy_n_epochs_per_batch=10,
        on_policy_n_minibatch_per_epoch=10,
        evaluation=True,
        evaluation_interval=50_000,
        evaluation_episodes=5,
        checkpoint=True,
        checkpoint_interval=100_000,
        loggers=["tensorboard"]   # or "wandb"
    )

    # 5. Run Experiment
    experiment = Experiment(
        task=task,
        algorithm_config=algorithm_config,
        model_config=model_config,
        critic_model_config=model_config, # Using same structure for critic
        config=experiment_config
    )

    print("Starting BenchMARL Training...")
    experiment.run()
    
    print("Training Finished. Check 'benchmarl_logs' folder.")

if __name__ == "__main__":
    try:
        train_benchmarl()
    except ImportError:
        print("BenchMARL or TorchRL not installed. Please install: 'pip install benchmarl torchrl'")
