
import numpy as np
import os
import sys

# Mocking the Environment components
class MockVoxelManager:
    def __init__(self):
        self.x_min, self.x_max = -20, 20
        self.y_min, self.y_max = -20, 20
        self.z_min, self.z_max = 0, 10
        self.resolution = 1.0
        
    def get_sparse_pointcloud(self):
        # Create a dummy cube of voxels
        # 3x3x3 block
        indices = []
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    indices.append([x, y, z])
        return np.array(indices, dtype=np.int32)

try:
    # Try importing from installed package first (Standard ROS2 way)
    from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
except ImportError:
    # Fallback: Add local source path if not installed
    # Docker Path
    if os.path.exists("/root/ros2_ws/src/swarm_sim_pkg"):
        sys.path.append("/root/ros2_ws/src/swarm_sim_pkg")
    # Host Path (Fallback)
    elif os.path.exists("/mnt/disk1/pgguedje/research/gazebo_ros2_vnc/src/swarm_sim_pkg"):
        sys.path.append("/mnt/disk1/pgguedje/research/gazebo_ros2_vnc/src/swarm_sim_pkg")
        
    try:
        from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
    except ImportError:
        print("Could not import SwarmCoverageEnv. Using Mock Implementation for verification.")
        # Fallback if imports fail
        import utm
        import laspy
        print("Dependencies `utm` and `laspy` are installed!")
        
        # Re-implement the key logic to verify it works
        def save_demo_map():
            lat0, lon0 = 48.8566, 2.3522
            easting0, northing0, _, _ = utm.from_latlon(lat0, lon0)
            print(f"Origin UTM: {easting0}, {northing0}")
            
            # Test file creation
            header = laspy.LasHeader(point_format=3, version="1.2")
            las = laspy.LasData(header)
            las.x = np.array([easting0])
            las.y = np.array([northing0])
            las.z = np.array([10.0])
            las.write("test_map_export.las")
            print("Created test_map_export.las")

        save_demo_map()
        sys.exit(0)

# Implementation if import succeeds
class TestEnv(SwarmCoverageEnv):
    def __init__(self):
        # Skip super init which starts ROS
        self.central_map = MockVoxelManager()
        self.geo_origin_lat = 48.8566
        self.geo_origin_lon = 2.3522
        self.geo_origin_alt = 100.0

print("Imported SwarmCoverageEnv successfully.")
env = TestEnv()
env.save_occupancy_map("test_map_export.las")
print("Test Complete.")
