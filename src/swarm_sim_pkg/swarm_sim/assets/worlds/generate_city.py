import random
import argparse

def generate_city_sdf(filename, args):
    header = """<?xml version="1.0" ?>
<sdf version="1.8">
  <world name="urban_city">
    <physics name="1ms" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"></plugin>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"></plugin>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"></plugin>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
        <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-wind-effects-system" name="gz::sim::systems::WindEffects"></plugin>

    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.5 0.1 -0.9</direction>
    </light>

    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><plane><normal>0 0 1</normal><size>200 200</size></plane></geometry>
          <surface>
            <friction>
              <ode>
                <mu>100</mu>
                <mu2>50</mu2>
              </ode>
            </friction>
          </surface>
        </collision>
        <visual name="visual">
          <geometry><plane><normal>0 0 1</normal><size>200 200</size></plane></geometry>
          <material><ambient>0.3 0.3 0.3 1</ambient><diffuse>0.3 0.3 0.3 1</diffuse></material>
        </visual>
      </link>
    </model>
"""
    
    footer = """
  </world>
</sdf>
"""
    
    buildings = ""
    
    # 1. Set Seed
    if args.seed is not None:
        random.seed(args.seed)
        print(f"Using seed: {args.seed}")
    
    # 2. Determine Number of Blocks based on Mode (if num_blocks not explicit or just use mode to scale)
    # The user asked for "mode full, medium, low".
    # We can use mode to set a multiplier or default count.
    
    base_count = args.num_blocks
    if args.mode == 'full':
        count = int(base_count * 1.5)
    elif args.mode == 'medium':
        count = base_count
    elif args.mode == 'low':
        count = int(base_count * 0.5)
    else:
        count = base_count

    buildings = ""
    generated_count = 0
    attempts = 0
    max_attempts = count * 50
    
    while generated_count < count and attempts < max_attempts:
        attempts += 1
        
        # Random Position
        x = random.uniform(-args.width/2, args.width/2)
        y = random.uniform(-args.length/2, args.length/2)
        
        # Check safe zone (middle area for drones)
        if abs(x) < args.safe_zone and abs(y) < args.safe_zone:
            continue
            
        w = random.uniform(3, 8)
        l = random.uniform(3, 8)
        h = random.uniform(args.min_height, args.max_height)
        
        buildings += f"""
    <model name="building_{generated_count}">
      <static>true</static>
      <pose>{x} {y} {h/2} 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>{w} {l} {h}</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>{w} {l} {h}</size></box></geometry>
          <material>
            <ambient>{random.random()} {random.random()} {random.random()} 1</ambient>
            <diffuse>{random.random()} {random.random()} {random.random()} 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
"""
        generated_count += 1

    with open(filename, "w") as f:
        f.write(header + buildings + footer)
    
    print(f"Generated {generated_count} buildings in {filename} (Mode: {args.mode})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a random city SDF")
    parser.add_argument("--output", default="generated_city.sdf", help="Output filename")
    parser.add_argument("--width", type=float, default=100.0, help="Width of the city area")
    parser.add_argument("--length", type=float, default=100.0, help="Length of the city area")
    parser.add_argument("--num_blocks", type=int, default=40, help="Base number of buildings (Medium)")
    parser.add_argument("--mode", type=str, default="medium", choices=['full', 'medium', 'low'], help="Density mode")
    parser.add_argument("--min_height", type=float, default=5.0, help="Min building height")
    parser.add_argument("--max_height", type=float, default=15.0, help="Max building height")
    parser.add_argument("--safe_zone", type=float, default=5.0, help="Safe zone radius/box around origin")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    generate_city_sdf(args.output, args)
