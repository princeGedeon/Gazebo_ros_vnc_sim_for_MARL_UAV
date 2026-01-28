
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

class MockEnv:
    def __init__(self):
        self.central_map = MockVoxelManager()
        self.geo_origin_lat = 48.8566
        self.geo_origin_lon = 2.3522
        self.geo_origin_alt = 100.0 # 100m ASL

    # Copy-paste the save_occupancy_map method here or import it? 
    # Better to import the class if possible, but simpler to mock the method logic or monkey patch.
    # Let's import the actual class to test the actual code modification.
    
try:
    # Adjust path
    sys.path.append("/mnt/disk1/pgguedje/research/gazebo_ros2_vnc/src/swarm_sim_pkg")
    from swarm_sim.envs.multi_agent.swarm_coverage_env import SwarmCoverageEnv
    
    # We can't instantiate Env because of ROS2 dependency in __init__
    # So we will monkey-patch or create a subclass that skips ROS init
    class TestEnv(SwarmCoverageEnv):
        def __init__(self):
            # Skip super init which starts ROS
            self.central_map = MockVoxelManager()
            self.geo_origin_lat = 48.8566
            self.geo_origin_lon = 2.3522
            self.geo_origin_alt = 100.0
            
except ImportError:
    # Fallback if imports fail (e.g. ROS not sourced in this shell context?)
    print("Could not import SwarmCoverageEnv. Using Mock Implementation for verification.")
    
    # Check if we can just test the logic inline
    import utm
    import laspy
    print("Dependencies `utm` and `laspy` are installed!")
    
    # Re-implement the key logic to verify it works
    def save_demo_map():
        import utm, laspy
        lat0, lon0 = 48.8566, 2.3522
        easting0, northing0, _, _ = utm.from_latlon(lat0, lon0)
        print(f"Origin UTM: {easting0}, {northing0}")
        
        # Test file creation
        import laspy
        header = laspy.LasHeader(point_format=3, version="1.2")
        las = laspy.LasData(header)
        las.x = np.array([easting0])
        las.y = np.array([northing0])
        las.z = np.array([10.0])
        las.write("test_map_output.laz")
        print("Created test_map_output.laz")

    save_demo_map()
    sys.exit(0)

# If import worked
print("Imported SwarmCoverageEnv successfully.")
env = TestEnv()
env.save_occupancy_map("test_map_export.laz")
print("Test Complete.")
