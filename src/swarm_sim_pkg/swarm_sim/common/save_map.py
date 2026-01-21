
import rclpy
from rclpy.node import Node
from octomap_msgs.srv import Octomap
import subprocess
import json
import os
import sys

class MapSaver(Node):
    def __init__(self):
        super().__init__('map_saver')
        
    def save(self, filename="swarm_map.bt"):
        self.get_logger().info(f"Saving map to {filename}...")
        
        # Method 1: Use octomap_server_node's built-in saver if available via service
        # Usually octomap_server provides 'octomap_binary' service but specific Saver tool is cli.
        # "ros2 run octomap_server octomap_saver_node --ros-args -p filename:=..."
        
        # We will wrap the subprocess call for simplicity and robust saving
        
        cmd = ["ros2", "run", "octomap_server", "octomap_saver_node", "-f", filename]
        try:
            # We assume map is on topic 'octomap_binary' or projected map
            # octomap_saver defaults to listening to 'octomap_binary'
            # We need to make sure we remap if our server is namespaced.
            # But wait, we have N servers or 1? In implementation plan we said 1 or N.
            # If 1 centralized for saving, we can assume 'octomap_binary' is available globally.
            
            # If we have N servers (uav_0/octomap_binary), we need to pick one or merge.
            # For this MVP, let's assume we listen to 'uav_0/octomap_binary' or user specifies.
            
            process = subprocess.Popen(cmd)
            process.wait()
            self.get_logger().info("Map data saved.")
            
            # Save Metadata
            meta = {
                "format": "octomap_binary",
                "crs": "EPSG:4326", # GPS
                "origin": {
                    "lat": 48.8566,
                    "lon": 2.3522,
                    "alt": 0.0
                },
                "resolution": 0.2
            }
            
            with open(filename + ".json", 'w') as f:
                json.dump(meta, f, indent=4)
                
            self.get_logger().info(f"Metadata saved to {filename}.json")
            
        except Exception as e:
            self.get_logger().error(f"Failed to save map: {e}")

def main():
    rclpy.init()
    saver = MapSaver()
    
    # Simple CLI usage: python3 save_map.py [filename]
    fname = sys.argv[1] if len(sys.argv) > 1 else "swarm_city.bt"
    
    saver.save(fname)
    
    rclpy.shutdown()

if __name__ == '__main__':
    main()
