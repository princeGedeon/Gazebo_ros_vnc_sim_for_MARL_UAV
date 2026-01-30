#!/usr/bin/env python3
import sys
import os

def generate_rviz_config(num_drones, output_path):
    """
    Generates a dynamic RViz configuration file for N drones.
    """
    
    # Header
    config = """Panels:
  - Class: rviz_common/Displays
    Help Height: 78
    Name: Displays
    Property Tree Widget:
      Expanded:
        - /Global Options1
        - /Robot Models1
        - /Sensors1
        - /2D Coverage1
        - /SLAM 3D1
      Splitter Ratio: 0.5
    Tree Height: 600
  - Class: rviz_common/Selection
    Name: Selection
  - Class: rviz_common/Tool Properties
    Expanded:
      - /2D Pose Estimate1
      - /2D Goal Pose1
    Name: Tool Properties
    Splitter Ratio: 0.58
  - Class: rviz_common/Views
    Expanded:
      - /Current View1
    Name: Views
    Splitter Ratio: 0.5
  - Class: rviz_common/Time
    Name: Time
    SyncMode: 0
    SyncSource: ""

Visualization Manager:
  Class: ""
  Displays:
    # Grid
    - Alpha: 0.3
      Cell Size: 1
      Class: rviz_default_plugins/Grid
      Color: 160; 160; 164
      Enabled: true
      Line Style:
        Line Width: 0.03
        Value: Lines
      Name: Grid
      Normal Cell Count: 0
      Offset:
        X: 0
        Y: 0
        Z: 0
      Plane: XY
      Plane Cell Count: 200
      Reference Frame: world
      Value: true
      
    # ============================================
    # GLOBAL COVERAGE MAP (2D & 3D)
    # ============================================
    - Class: rviz_default_plugins/Group
      Name: 2D Coverage
      Displays:
        # Global Occupancy Grid (2D Projection)
        - Alpha: 0.7
          Class: rviz_default_plugins/Map
          Color Scheme: map
          Draw Behind: false
          Enabled: true
          Name: Global Occupancy 2D
          Topic:
            Depth: 5
            Durability Policy: Volatile
            History Policy: Keep Last
            Reliability Policy: Reliable
            Value: /coverage_map_2d
          Update Topic:
            Depth: 5
            Durability Policy: Volatile
            History Policy: Keep Last
            Reliability Policy: Reliable
            Value: /coverage_map_2d_updates
          Use Timestamp: false
          Value: true
          
        # Voxel Grid (3D Points)
        - Alpha: 1.0
          Autocompute Intensity Bounds: true
          Autocompute Value Bounds:
            Max Value: 10
            Min Value: -10
            Value: true
          Axis: Z
          Channel Name: intensity
          Class: rviz_default_plugins/PointCloud2
          Color: 255; 0; 0
          Color Transformer: FlatColor
          Decay Time: 0
          Enabled: true
          Invert Rainbow: false
          Max Color: 255; 255; 255
          Min Color: 0; 0; 0
          Name: Voxel Map (3D)
          Position Transformer: XYZ
          Selectable: true
          Size (Pixels): 3
          Size (m): 0.1
          Style: Points
          Topic:
            Depth: 5
            Durability Policy: Volatile
            History Policy: Keep Last
            Reliability Policy: Best Effort
            Value: /coverage_map_voxels
          Use Fixed Frame: true
          Use rainbow: false
          Value: true
      Enabled: true

    # ============================================
    # ROBOT MODELS & SENSORS (Generated)
    # ============================================
"""

    # Generate per-drone sections
    colors = ["255; 255; 0", "0; 255; 255", "255; 0; 255", "50; 255; 50", "50; 50; 255"]
    
    # 1. Robot Models
    config += "    - Class: rviz_default_plugins/Group\n"
    config += "      Name: Robot Models\n"
    config += "      Displays:\n"
    
    for i in range(num_drones):
        config += f"""        - Alpha: 1
          Class: rviz_default_plugins/RobotModel
          Description Topic:
            Value: /uav_{i}/robot_description
          Enabled: true
          Name: UAV {i}
          TF Prefix: uav_{i}
          Value: true
          Visual Enabled: true
"""
    config += "      Enabled: true\n\n"

    # 2. Sensors (LiDAR)
    config += "    - Class: rviz_default_plugins/Group\n"
    config += "      Name: Sensors (LiDAR)\n"
    config += "      Displays:\n"
    
    for i in range(num_drones):
        color = colors[i % len(colors)]
        config += f"""        - Alpha: 1.0
          Class: rviz_default_plugins/PointCloud2
          Color: {color}
          Color Transformer: FlatColor
          Enabled: true
          Name: LiDAR UAV {i}
          Size (m): 0.1
          Style: Points
          Topic:
            Value: /uav_{i}/velodyne_points
          Value: true
"""
    config += "      Enabled: true\n\n"
    
    # 3. Path/Trajectory
    config += "    - Class: rviz_default_plugins/Group\n"
    config += "      Name: Trajectories\n"
    config += "      Displays:\n"
    
    for i in range(num_drones):
        color = colors[i % len(colors)]
        config += f"""        - Alpha: 1
          Buffer Length: 100
          Class: rviz_default_plugins/Path
          Color: {color}
          Enabled: true
          Line Style: Lines
          Line Width: 0.05
          Name: Path UAV {i}
          Topic:
            Value: /uav_{i}/path
          Value: true
"""
    config += "      Enabled: true\n\n"
    
    # Limit TF to avoid clutter
    config += """    # ============================================
    # VISUALIZATION MARKERS (NFZ & Stations)
    # ============================================
    - Class: rviz_default_plugins/Group
      Name: Environment Markers
      Displays:
        - Class: rviz_default_plugins/MarkerArray
          Enabled: true
          Name: No-Fly Zones (NFZ)
          Namespaces:
            nfz: true
          Topic:
            Value: /comm_range_markers
          Value: true
        
        - Class: rviz_default_plugins/MarkerArray
          Enabled: true
          Name: Stations
          Namespaces:
            stations: true
          Topic:
            Value: /comm_range_markers
          Value: true
      Enabled: true

    # ============================================
    # TF FRAMES
    # ============================================
    - Class: rviz_default_plugins/TF
      Enabled: true
      Frame Timeout: 15
      Frames:
        All Enabled: false
        world:
          Value: true
"""
    for i in range(num_drones):
        config += f"""        uav_{i}:
          Value: true
        uav_{i}/base_link:
          Value: true
"""
    
    config += """      Marker Scale: 1
      Name: TF
      Show Arrows: true
      Show Axes: true
      Show Names: false
      Update Interval: 0
      Value: true
  
  Enabled: true
  Global Options:
    Background Color: 48; 48; 48
    Fixed Frame: world
    Frame Rate: 30
  Name: root
  Tools:
    - Class: rviz_default_plugins/Interact
      Hide Inactive Objects: true
    - Class: rviz_default_plugins/MoveCamera
    - Class: rviz_default_plugins/Select
    - Class: rviz_default_plugins/FocusCamera
    - Class: rviz_default_plugins/Measure
    - Class: rviz_default_plugins/SetInitialPose
    - Class: rviz_default_plugins/SetGoal
    - Class: rviz_default_plugins/PublishPoint
  Transformation:
    Current:
      Class: rviz_default_plugins/TF
  Value: true
  Views:
    Current:
      Class: rviz_default_plugins/Orbit
      Distance: 60
      Focal Point:
        X: 0
        Y: 0
        Z: 0
      Name: Current View
      Pitch: 0.78
      Target Frame: <Fixed Frame>
      Value: Orbit (rviz)
      Yaw: 0.78
  Window Geometry:
    Height: 1000
    Width: 1600
    X: 50
    Y: 50
"""

    with open(output_path, 'w') as f:
        f.write(config)
    
    print(f"Generated dynamic RViz config for {num_drones} drones at: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: generate_rviz.py <num_drones> <output_path>")
        sys.exit(1)
        
    num_drones = int(sys.argv[1])
    output_path = sys.argv[2]
    
    generate_rviz_config(num_drones, output_path)
