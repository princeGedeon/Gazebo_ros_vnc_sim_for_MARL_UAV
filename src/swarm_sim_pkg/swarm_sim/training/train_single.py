
import gymnasium as gym
import rclpy
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from uav_env import SingleUAVEnv
import os

def main():
    # 1. Initialize ROS context (if not done inside Env, but Env checks it)
    # 2. Create Environment
    env = SingleUAVEnv()
    
    # 3. Check Custom Env (Sanity check)
    print("Checking environment compatibility...")
    try:
        check_env(env)
        print("Environment check passed!")
    except Exception as e:
        print(f"Environment check warning: {e}")
        # Sometimes warnings happen (e.g. render modes), proceed if minor.

    # 4. Define Agent (PPO)
    tensorboard_log = "./uav_tensorboard/"
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=tensorboard_log)

    # 5. Train
    print("Starting training...")
    try:
        model.learn(total_timesteps=10000)
        print("Training complete.")
    except KeyboardInterrupt:
        print("Training interrupted.")
    
    # 6. Save Model
    model.save("ppo_uav_agent")
    print("Model saved to ppo_uav_agent.zip")
    
    # 7. Close
    env.close()

if __name__ == "__main__":
    main()
