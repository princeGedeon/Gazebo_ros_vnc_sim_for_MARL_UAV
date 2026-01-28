
import numpy as np
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import ColorRGBA
import struct

class VoxelVisualizer(Node):
    """
    ROS 2 Node helper that publishes the visited voxels as markers for RViz.
    """
    def __init__(self):
        super().__init__('voxel_visualizer')
        self.pub_voxels = self.create_publisher(PointCloud2, '/coverage_map_voxels', 10)
        self.pub_markers = self.create_publisher(MarkerArray, '/comm_range_markers', 10)

    def publish_voxels(self, grid_or_sparse, resolution, x_min, y_min, z_min):
        """
        Publishes the Voxel Grid (Dense or Sparse).
        """
        msg = PointCloud2()
        msg.header.frame_id = "world" # Changed from "map" to "world" to match original frame_id
        msg.header.stamp = self.get_clock().now().to_msg() # Changed from self.clock.now() to self.get_clock().now()
        
        points = []
        
        # Determine format (since we switched to Sparse Set in VoxelManager)
        # grid_or_sparse can be np.array(dense) or set(sparse)
        
        if isinstance(grid_or_sparse, np.ndarray) and grid_or_sparse.ndim == 3:
            # OLD Dense Logic (kept for compatibility)
            indices = np.argwhere(grid_or_sparse == 1)
            for idx in indices:
                gx, gy, gz = idx
                px = x_min + gx * resolution + resolution/2
                py = y_min + gy * resolution + resolution/2
                pz = z_min + gz * resolution + resolution/2
                points.append([px, py, pz])
                
        elif isinstance(grid_or_sparse, list) or isinstance(grid_or_sparse, set):
            # NEW Sparse Logic
            for (gx, gy, gz) in grid_or_sparse:
                px = x_min + gx * resolution + resolution/2
                py = y_min + gy * resolution + resolution/2
                pz = z_min + gz * resolution + resolution/2
                points.append([px, py, pz])
        
        if not points:
            return

        # Create PC2 fields
        # Simple slow python packing debug only
        # Real impl uses point_cloud2.create_cloud_xyz32
        
        msg.height = 1
        msg.width = len(points)
        msg.fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1)
        ]
        msg.is_bigendian = False
        msg.point_step = 12
        msg.row_step = 12 * len(points)
        msg.is_dense = True
        
        buffer = []
        for p in points:
            buffer.append(struct.pack('fff', float(p[0]), float(p[1]), float(p[2])))
        
        msg.data = b''.join(buffer)
        
        self.pub_voxels.publish(msg)

    def publish_comm_range(self, positions, range_radius=5.0):
        """
        Publishes ellipses/circles around agents to visualize communication range.
        positions: dict {agent_id: np.array([x,y,z])}
        """
        marker_array = MarkerArray()
        
        id_counter = 0
        for agent_id, pos in positions.items():
            marker = Marker()
            marker.header.frame_id = "world" # Changed from "map" to "world" to match original frame_id
            marker.header.stamp = self.get_clock().now().to_msg() # Changed from self.clock.now() to self.get_clock().now()
            marker.ns = "comm_range"
            marker.id = id_counter
            id_counter += 1
            
            marker.type = Marker.CYLINDER
            marker.action = Marker.ADD
            
            # Position
            marker.pose.position.x = float(pos[0])
            marker.pose.position.y = float(pos[1])
            marker.pose.position.z = float(pos[2]) # Or 0 if we want ground projection
            
            # Scale (Diameter = 2 * Radius)
            marker.scale.x = range_radius * 2.0
            marker.scale.y = range_radius * 2.0
            marker.scale.z = 0.1 # Thin disk
            
            # Color (Blue transparent)
            marker.color.a = 0.2
            marker.color.r = 0.0
            marker.color.g = 0.5
            marker.color.b = 1.0
            
            marker_array.markers.append(marker)
            
        self.pub_markers.publish(marker_array)

    def publish_stations(self, station_positions):
        """
        Visualizes Ground Stations as Green Spheres.
        station_positions: list or array of [x, y]
        """
        marker_array = MarkerArray()
        id_counter = 1000 # Offset to avoid conflict with drones
        
        for i, pos in enumerate(station_positions):
            marker = Marker()
            marker.header.frame_id = "world"
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = "stations"
            marker.id = id_counter + i
            
            marker.type = Marker.SPHERE
            marker.action = Marker.ADD
            
            marker.pose.position.x = float(pos[0])
            marker.pose.position.y = float(pos[1])
            marker.pose.position.z = 0.5 # Slightly above ground
            
            marker.scale.x = 2.0 # 2m radius zone visual
            marker.scale.y = 2.0
            marker.scale.z = 2.0
            
            # Green (Charging/Safe)
            marker.color.a = 0.6
            marker.color.r = 0.0
            marker.color.g = 1.0
            marker.color.b = 0.0
            
            marker_array.markers.append(marker)
            
        self.pub_markers.publish(marker_array)

            marker_array.markers.append(marker)
            
        self.pub_markers.publish(marker_array)

    def get_agent_color(self, agent_id):
        """Returns (r, g, b) based on agent ID suffix."""
        try:
            # simple hash or index mapping
            # uav_0 -> Red, uav_1 -> Green, uav_2 -> Blue, etc.
            idx = int(agent_id.split('_')[-1])
            colors = [
                (1.0, 0.0, 0.0), # Red
                (0.0, 1.0, 0.0), # Green
                (0.0, 0.0, 1.0), # Blue
                (1.0, 1.0, 0.0), # Yellow
                (0.0, 1.0, 1.0), # Cyan
                (1.0, 0.0, 1.0)  # Magenta
            ]
            return colors[idx % len(colors)]
        except:
            return (1.0, 1.0, 1.0) # White

    def publish_boundaries(self, x_min, x_max, y_min, y_max, z_max=10.0):
        """
        Visualizes the workspace limits as a Line Strip.
        """
        marker = Marker()
        marker.header.frame_id = "world"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "boundary"
        marker.id = 0
        marker.type = Marker.LINE_STRIP
        marker.action = Marker.ADD
        marker.scale.x = 0.2 # Thickness
        
        # White Boundary
        marker.color.a = 1.0
        marker.color.r = 1.0
        marker.color.g = 1.0
        marker.color.b = 1.0
        
        # Draw Box at Ground and Ceiling
        corners = [
            (x_min, y_min), (x_max, y_min), 
            (x_max, y_max), (x_min, y_max), 
            (x_min, y_min) # Close loop
        ]
        
        # Ground Loop
        for x, y in corners:
            marker.points.append(Point(x=float(x), y=float(y), z=0.0))
            
        # Ceiling Loop (Optional, to show 3D volume)
        for x, y in corners:
            marker.points.append(Point(x=float(x), y=float(y), z=float(z_max)))

        # Vertical Pillars at corners
        # (Requires LINE_LIST or just assume user infers volume)
        # For simple LINE_STRIP, we just drew two loops.
        
        marker_array = MarkerArray()
        marker_array.markers.append(marker)
        self.pub_markers.publish(marker_array)

    def publish_lidar_cone(self, uav_poses):
        """
        Visualizes Lidar Down FoV with Unique Agent Colors.
        uav_poses: dict {agent_id: state}
        """
        marker_array = MarkerArray()
        id_counter = 2000 
        
        height = 5.0
        fov_radius = 2.5 
        
        for agent_id, state in uav_poses.items():
            pos = state[:3]
            r, g, b = self.get_agent_color(agent_id)
            
            marker = Marker()
            marker.header.frame_id = "world"
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = f"lidar_cone_{agent_id}" # Namespace per agent to avoid flickering
            marker.id = id_counter
            id_counter += 1
            
            marker.type = Marker.LINE_LIST
            marker.action = Marker.ADD
            marker.scale.x = 0.05 
            
            marker.color.a = 0.8
            marker.color.r = r
            marker.color.g = g
            marker.color.b = b
            
            apex = Point(x=float(pos[0]), y=float(pos[1]), z=float(pos[2]))
            
            corners = [
                (pos[0]+fov_radius, pos[1]+fov_radius, pos[2]-height),
                (pos[0]-fov_radius, pos[1]+fov_radius, pos[2]-height),
                (pos[0]-fov_radius, pos[1]-fov_radius, pos[2]-height),
                (pos[0]+fov_radius, pos[1]-fov_radius, pos[2]-height)
            ]
            
            # Edges from Apex
            for c in corners:
                p_corn = Point(x=float(c[0]), y=float(c[1]), z=float(c[2]))
                marker.points.append(apex)
                marker.points.append(p_corn)
                
            # Base edges
            c_pts = [Point(x=float(c[0]), y=float(c[1]), z=float(c[2])) for c in corners]
            for j in range(4):
                marker.points.append(c_pts[j])
                marker.points.append(c_pts[(j+1)%4])
                
            marker_array.markers.append(marker)
            
        self.pub_markers.publish(marker_array)

    def publish_nfz(self, nfz_list):
        """
        Visualizes No-Fly Zones as Red Cylinders.
        """
        marker_array = MarkerArray()
        id_counter = 3000
        
        for i, (x, y, r) in enumerate(nfz_list):
            marker = Marker()
            marker.header.frame_id = "world"
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = "nfz"
            marker.id = id_counter + i
            
            marker.type = Marker.CYLINDER
            marker.action = Marker.ADD
            
            marker.pose.position.x = float(x)
            marker.pose.position.y = float(y)
            marker.pose.position.z = 5.0 
            
            marker.scale.x = float(r) * 2.0
            marker.scale.y = float(r) * 2.0
            marker.scale.z = 10.0 
            
            marker.color.a = 0.5
            marker.color.r = 1.0
            marker.color.g = 0.0
            marker.color.b = 0.0
            
            marker_array.markers.append(marker)
            
        self.pub_markers.publish(marker_array)
