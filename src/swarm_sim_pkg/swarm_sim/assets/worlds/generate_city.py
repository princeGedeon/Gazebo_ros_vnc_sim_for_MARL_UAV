import random
import argparse

def generate_city_sdf(filename, args):
    header = """<?xml version="1.0" ?>
<sdf version="1.8">
  <world name="urban_city_rich">
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
    
    content = ""
    
    if args.seed is not None:
        random.seed(args.seed)
        print(f"Using seed: {args.seed}")
    
    # Grid Parameters
    block_size = 20.0 # Meters per block (building area)
    road_width = 8.0  # Meters for road
    grid_step = block_size + road_width
    
    num_x = int(args.width / grid_step)
    num_y = int(args.length / grid_step)
    
    print(f"Generating Rich City: {num_x}x{num_y} Grid. Road Width: {road_width}m")

    # Safe Zone: Rectangular for 3 Stations (-15 to +15 X, -5 to +5 Y)
    def is_safe(gx, gy):
        # Allow +/- 15m in X and +/- 8m in Y
        if abs(gx) < 18.0 and abs(gy) < 10.0:
            return True
        return False

    model_count = 0

    # Generate Grid
    for i in range(-num_x//2, num_x//2 + 1):
        for j in range(-num_y//2, num_y//2 + 1):
            
            center_x = i * grid_step
            center_y = j * grid_step
            
            # 1. Intersection (Roundabout or Crossing)
            # Create a "Road" tile (Using flattened boxes for visual road)
            # Center tile (Intersection)
            
            # Intersection Visual (Dark Grey Asphalt)
            content += f"""
    <model name="road_inter_{i}_{j}">
      <static>true</static>
      <pose>{center_x} {center_y} 0.01 0 0 0</pose>
      <link name="link">
        <visual name="vis">
            <geometry><box><size>{road_width} {road_width} 0.02</size></box></geometry>
            <material><ambient>0.1 0.1 0.1 1</ambient><diffuse>0.1 0.1 0.1 1</diffuse></material>
        </visual>
      </link>
    </model>
"""
            
            # Roundabout Feature? (Every 2nd intersection)
            if (i % 2 == 0) and (j % 2 == 0) and not is_safe(center_x, center_y):
                 # Spawn Roundabout Island
                 content += f"""
    <model name="roundabout_{i}_{j}">
      <static>true</static>
      <pose>{center_x} {center_y} 0.3 0 0 0</pose>
      <link name="link">
        <collision name="col">
           <geometry><cylinder><radius>{road_width/3}</radius><length>0.6</length></cylinder></geometry>
        </collision>
        <visual name="vis">
           <geometry><cylinder><radius>{road_width/3}</radius><length>0.6</length></cylinder></geometry>
           <material><ambient>0.2 0.6 0.2 1</ambient><diffuse>0.2 0.6 0.2 1</diffuse></material>
        </visual>
      </link>
    </model>
"""

            # 2. Roads Connecting
            # East Road
            content += f"""
    <model name="road_h_{i}_{j}">
      <static>true</static>
      <pose>{center_x + grid_step/2} {center_y} 0.01 0 0 0</pose>
      <link name="link">
        <visual name="vis">
            <geometry><box><size>{block_size} {road_width} 0.02</size></box></geometry>
            <material><ambient>0.2 0.2 0.2 1</ambient><diffuse>0.2 0.2 0.2 1</diffuse></material>
        </visual>
      </link>
    </model>
    <model name="road_v_{i}_{j}">
      <static>true</static>
      <pose>{center_x} {center_y + grid_step/2} 0.01 0 0 0</pose>
      <link name="link">
        <visual name="vis">
            <geometry><box><size>{road_width} {block_size} 0.02</size></box></geometry>
            <material><ambient>0.2 0.2 0.2 1</ambient><diffuse>0.2 0.2 0.2 1</diffuse></material>
        </visual>
      </link>
    </model>
"""

            # 3. Building Block (The Quadrants around intersection?)
            # Actually grid logic usually puts building in the "cell".
            # My logic: center_x is intersection. center_x + step/2 is road.
            # Building center is center_x + step/2, center_y + step/2 (The block center)
            
            block_center_x = center_x + grid_step/2
            block_center_y = center_y + grid_step/2
            
            if is_safe(block_center_x, block_center_y):
                continue
                
            # Randomize Building Type
            b_type = random.choice(['tall', 'house', 'cylinder', 'park'])
            
            if b_type == 'park':
                # Green Flat Area
                content += f"""
    <model name="park_{i}_{j}">
      <static>true</static>
      <pose>{block_center_x} {block_center_y} 0.05 0 0 0</pose>
      <link name="link">
        <visual name="vis">
            <geometry><box><size>{block_size-2} {block_size-2} 0.1</size></box></geometry>
            <material><ambient>0.1 0.8 0.1 1</ambient><diffuse>0.1 0.8 0.1 1</diffuse></material>
        </visual>
      </link>
    </model>
"""
            else:
                # Building
                height = random.uniform(args.min_height, args.max_height) if b_type != 'house' else random.uniform(3, 6)
                width = random.uniform(block_size*0.4, block_size*0.8)
                depth = random.uniform(block_size*0.4, block_size*0.8)
                
                color = f"{random.random()} {random.random()} {random.random()} 1"
                
                shape_xml = ""
                if b_type == 'cylinder':
                     shape_xml = f"<cylinder><radius>{width/2}</radius><length>{height}</length></cylinder>"
                else:
                     shape_xml = f"<box><size>{width} {depth} {height}</size></box>"
                
                content += f"""
    <model name="bldg_{model_count}">
      <static>true</static>
      <pose>{block_center_x} {block_center_y} {height/2} 0 0 0</pose>
      <link name="link">
        <collision name="col">
           <geometry>{shape_xml}</geometry>
        </collision>
        <visual name="vis">
           <geometry>{shape_xml}</geometry>
           <material><ambient>{color}</ambient><diffuse>{color}</diffuse></material>
        </visual>
      </link>
    </model>
"""
                # Add "Door" simulation? (Small box subtraction or different color patch)
                # Adding a small black box at bottom front
                content += f"""
    <model name="door_{model_count}">
      <static>true</static>
      <pose>{block_center_x} {block_center_y - depth/2 - 0.1} 1.0 0 0 0</pose>
      <link name="link">
        <visual name="vis">
           <geometry><box><size>{width/3} 0.2 2.0</size></box></geometry>
           <material><ambient>0 0 0 1</ambient><diffuse>0 0 0 1</diffuse></material>
        </visual>
      </link>
    </model>
"""
                model_count += 1

    with open(filename, "w") as f:
        f.write(header + content + footer)
    
    print(f"Generated Rich City in {filename} with {model_count} buildings and roads.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a random city SDF")
    parser.add_argument("--output", default="generated_city.sdf", help="Output filename")
    parser.add_argument("--width", type=float, default=250.0, help="Width of the city area")
    parser.add_argument("--length", type=float, default=250.0, help="Length of the city area")
    parser.add_argument("--num_blocks", type=int, default=40, help="Base number of buildings (Medium) - Unused in Grid Mode")
    parser.add_argument("--mode", type=str, default="medium", choices=['full', 'medium', 'low'], help="Density mode")
    parser.add_argument("--min_height", type=float, default=5.0, help="Min building height")
    parser.add_argument("--max_height", type=float, default=25.0, help="Max building height")
    parser.add_argument("--safe_zone", type=float, default=15.0, help="Safe zone radius/box around origin")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    generate_city_sdf(args.output, args)
