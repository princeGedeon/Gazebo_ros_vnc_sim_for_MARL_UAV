
import numpy as np
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
from std_msgs.msg import ColorRGBA

class VoxelVisualizer(Node):
    """
    ROS 2 Node helper that publishes the visited voxels as markers for RViz.
    """
    def __init__(self):
        super().__init__('voxel_visualizer')
        self.marker_pub = self.create_publisher(MarkerArray, '/coverage_map', 10)

    def publish_voxels(self, grid, voxel_size, x_min, y_min, z_min):
        """
        grid: 3D numpy array (1 = visited)
        """
        markers = MarkerArray()
        
        # Optimize: Publish only *new* or use a persistent marker with points (CUBE_LIST)
        msg = Marker()
        msg.header.frame_id = "world"
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.ns = "visited_voxels"
        msg.id = 0
        msg.type = Marker.CUBE_LIST
        msg.action = Marker.ADD
        msg.scale.x = voxel_size
        msg.scale.y = voxel_size
        msg.scale.z = voxel_size
        msg.color.a = 0.6
        msg.color.r = 0.0
        msg.color.g = 1.0
        msg.color.b = 0.0
        
        # Iterate and find visited
        indices = np.argwhere(grid == 1)
        for idx in indices:
            gx, gy, gz = idx
            wx = x_min + gx * voxel_size + voxel_size/2
            wy = y_min + gy * voxel_size + voxel_size/2
            wz = z_min + gz * voxel_size + voxel_size/2
            
            p = Point()
            p.x = float(wx)
            p.y = float(wy)
            p.z = float(wz)
            msg.points.append(p)
            
        markers.markers.append(msg)
        self.marker_pub.publish(markers)
