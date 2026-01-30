#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose
import subprocess
import time
import sys

# NFZ Configuration (matches Environment default/medium)
# Case 2 (Medium) assumes 3 NFZs
# We can pass this as args later. For now, hardcoding the requested "Medium" setup or making it configurable.

def spawn_cylinder(name, x, y, radius, height=20.0, color="1 0 0 0.5"):
    # Generate simple SDF for a visual-only cylinder
    sdf = f"""<?xml version='1.0'?>
<sdf version='1.6'>
  <model name='{name}'>
    <static>true</static>
    <link name='link'>
      <pose>0 0 {height/2} 0 0 0</pose>
      <visual name='visual'>
        <geometry>
          <cylinder>
            <radius>{radius}</radius>
            <length>{height}</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>{color}</ambient>
          <diffuse>{color}</diffuse>
        </material>
        <transparency>0.5</transparency>
      </visual>
    </link>
  </model>
</sdf>"""
    
    cmd = [
        'ros2', 'run', 'ros_gz_sim', 'create',
        '-name', name,
        '-string', sdf,
        '-x', str(x), '-y', str(y), '-z', '0'
    ]
    print(f"Spawning {name} at {x}, {y}...")
    subprocess.Popen(cmd)

def spawn_boundary_pole(name, x, y, z_min, z_max):
    height = z_max - z_min
    z_center = z_min + height/2
    # Thin pole
    spawn_cylinder(name, x, y, 0.1, height=height, color="1 1 1 0.8")
    # Adjust Z? my spawn_cylinder assumes z=0 base.
    # Actually spawn_cylinder sets pose z=height/2. 
    # To support z_min start, we need to shift.
    # Let's just use spawn_cylinder for NFZ for now.

def main():
    rclpy.init()
    
    # Wait for simulation to start
    time.sleep(5.0)
    
    # Define NFZs (matches Environment 'medium' or default random logic?)
    # Since Env generates them randomly in 'default', we can't perfectly match unless we:
    # 1. Read the Env config
    # 2. Or force fixed NFZs for these scenarios.
    
    # For the "Case" scripts, we should probably output the NFZ config to a file or param.
    # User asked: "3 nfz et sur le gazebo mes un signe".
    # I will define fixed NFZs for the "Medium" scenario so they are consistent.
    
    nfzs = [
        ("nfz_1", 5.0, 5.0, 3.0),
        ("nfz_2", -8.0, 2.0, 2.5),
        ("nfz_3", 2.0, -8.0, 4.0)
    ]
    
    # 1. Spawn NFZs
    for name, x, y, r in nfzs:
        spawn_cylinder(name, x, y, r)
        
    # 2. Spawn Workspace Boundaries (Corners)
    # 40x40m Box centered at 0
    box_corners = [
        ("bound_1", -20, -20),
        ("bound_2", 20, -20),
        ("bound_3", 20, 20),
        ("bound_4", -20, 20)
    ]
    for name, x, y in box_corners:
        # Spawn tall poles (30m high)
        spawn_cylinder(name, x, y, radius=0.2, height=30.0, color="1 1 1 0.5")

    print(f"Spawned {len(nfzs)} NFZs and 4 Boundary Poles.")

if __name__ == '__main__':
    main()
