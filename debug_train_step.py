
import rclpy
from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv

def debug_run():
    print("DEBUG: Instantiating Env...")
    env = SwarmCoverageEnv(num_drones=3, max_steps=10)
    
    print("DEBUG: Resetting Env...")
    try:
        obs, info = env.reset()
        print("DEBUG: Reset Success. Obs keys:", obs.keys())
    except Exception as e:
        print(f"DEBUG: Reset FAILED with {e}")
        import traceback
        traceback.print_exc()
        return

    print("DEBUG: Stepping Env...")
    try:
        # Dummy actions
        actions = {agent: env.action_space(agent).sample() for agent in env.agents}
        obs, rew, term, trunc, info = env.step(actions)
        print("DEBUG: Step Success. Reward keys:", rew.keys())
    except Exception as e:
        print(f"DEBUG: Step FAILED with {e}")
        import traceback
        traceback.print_exc()
        return

    print("DEBUG: Closing...")
    env.close()

if __name__ == "__main__":
    debug_run()
