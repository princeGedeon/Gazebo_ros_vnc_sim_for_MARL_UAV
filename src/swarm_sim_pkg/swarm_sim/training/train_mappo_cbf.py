
import os
import ray
import numpy as np
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.env.wrappers.pettingzoo_env import ParallelPettingZooEnv
from ray.tune.registry import register_env
from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
from scipy.optimize import minimize

class SafetyWrapper(SwarmCoverageEnv):
    """
    Wraps the SwarmCoverageEnv to apply a Control Barrier Function (CBF) Safety Layer
    to the actions before executing them.
    Implements: Layered Safety MARL (Safe Action Projection).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gamma = 1.0 # CBF Decay Rate

    def step(self, actions):
        safe_actions = {}
        for agent, action in actions.items():
            if agent in self.uavs:
                # 1. Get State
                uav = self.uavs[agent]
                pos = uav.position
                
                # 2. Solve QP/Optimization for Safe Action
                safe_act = self._solve_cbf(pos, action)
                safe_actions[agent] = safe_act
            else:
                safe_actions[agent] = action
        
        # Execute Safe Actions
        return super().step(safe_actions)

    def _solve_cbf(self, pos, u_ref):
        """
        Solve: min ||u - u_ref||^2
        Subject into:
          h_i(x) + grad(h_i) * u >= -gamma * h_i(x)
        """
        # Constraints list
        cons = []
        
        x, y, z = pos
        vx_ref, vy_ref, vz_ref, yaw_ref = u_ref
        
        # 1. Altitude Min
        # h = z - z_min
        h_min = z - self.min_height
        # grad = [0, 0, 1, 0]
        # cond: vz >= -gamma * h
        cons.append({'type': 'ineq', 'fun': lambda u: u[2] + self.gamma * h_min})

        # 2. Altitude Max
        # h = z_max - z
        h_max = self.max_height - z
        # grad = [0, 0, -1, 0]
        # cond: -vz >= -gamma * h  => vz <= gamma * h
        cons.append({'type': 'ineq', 'fun': lambda u: (self.gamma * h_max) - u[2]})
        
        # 3. NFZ (Cylinders)
        for (cx, cy, r) in self.nfz_list:
            # h = dist^2 - R^2
            dist_sq = (x - cx)**2 + (y - cy)**2
            h_nfz = dist_sq - (r + 0.5)**2 # Add buffer
            
            # grad h = [2(x-cx), 2(y-cy), 0, 0]
            # cond: grad * u >= -gamma * h
            def cbf_nfz(u, cx=cx, cy=cy, h=h_nfz):
                dot_prod = 2*(x-cx)*u[0] + 2*(y-cy)*u[1]
                return dot_prod + self.gamma * h
            
            cons.append({'type': 'ineq', 'fun': cbf_nfz})

        # Solving QP using SLSQP
        # Objective: sum((u - u_ref)^2)
        def objective(u):
            return np.sum((u - u_ref)**2)
            
        # Initial guess = u_ref
        res = minimize(objective, u_ref, constraints=cons, method='SLSQP', bounds=[(-1,1), (-1,1), (-1,1), (-1,1)])
        
        if res.success:
            return res.x.astype(np.float32)
        else:
            # If solver fails (infeasible), usually stop (0,0,0) or best effort
            # In CBF theory, feasibility is guaranteed if started in safe set.
            # Fallback: Zero velocity (hover)
            # But zero might violate min_height if we are below? 
            # Best effort: u_ref
            return u_ref # Or np.zeros(4)

def env_creator_cbf(config):
    # Instantiate Wrapper instead of base class
    env = SafetyWrapper(
        num_drones=3,
        nfz_config=config.get("nfz_config", 'default'),
        min_height=2.0,
        max_height=10.0,
        max_steps=500 
    )
    return env

def train_cbf():
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
        return env_creator_cbf(config)

    register_env("swarm_coverage_cbf", lambda config: ParallelPettingZooEnv(env_creator_wrapper(config)))

    config = (
        PPOConfig()
        .environment(
            "swarm_coverage_cbf", 
            env_config={
                "num_drones": args.num_drones,
                "nfz_config": "default"
            }
        )
        .framework("torch")
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

    print(f"Starting Layered Safety (CBF) MAPPO Training...")
    print(f"Hyperparams: Iterations={args.iterations}, Steps/Ep={args.max_steps}, Drones={args.num_drones}")
    
    # Init Ray with Dashboard exposed
    ray.init(dashboard_host="0.0.0.0", include_dashboard=True, ignore_reinit_error=True)
    
    tuner = tune.Tuner(
        "PPO",
        param_space=config.to_dict(),
        run_config=tune.RunConfig(
        run_config=tune.RunConfig(
            name="mappo_cbf",
            stop={"timesteps_total": args.total_timesteps} if args.total_timesteps > 0 else {"training_iteration": args.iterations},
            checkpoint_config=tune.CheckpointConfig(checkpoint_frequency=args.checkpoint_freq),
            storage_path=os.path.abspath(args.output_dir)
        ),
    )
    
    tuner.fit()
    print("CBF Training Completed.")

if __name__ == "__main__":
    train_cbf()
