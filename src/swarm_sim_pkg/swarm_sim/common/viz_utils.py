
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
        from nav_msgs.msg import OccupancyGrid
        self.pub_2d_map = self.create_publisher(OccupancyGrid, '/coverage_map_2d', 10)

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

        # Optimization: Use Numpy for fast packing
        # points is currently a list of [x, y, z]. Convert to float32 array.
        points_arr = np.array(points, dtype=np.float32)

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
        
        # Fast binary conversion
        msg.data = points_arr.tobytes()
        
        self.pub_voxels.publish(msg)

    def publish_2d_map(self, grid_or_sparse, resolution, x_min, y_min, z_min, x_max, y_max):
        """
        Publishes a 2D OccupancyGrid by projecting the 3D Voxel Map downwards.
        Useful for visualizing coverage evolution clearly.
        """
        from nav_msgs.msg import OccupancyGrid
        
        msg = OccupancyGrid()
        msg.header.frame_id = "world"
        msg.header.stamp = self.get_clock().now().to_msg()
        
        # Grid Dimensions
        width_m = x_max - x_min
        height_m = y_max - y_min
        
        cells_x = int(width_m / resolution)
        cells_y = int(height_m / resolution)
        
        msg.info.resolution = resolution
        msg.info.width = cells_x
        msg.info.height = cells_y
        msg.info.origin.position.x = float(x_min)
        msg.info.origin.position.y = float(y_min)
        msg.info.origin.position.z = 0.0
        
        # Initialize grid with -1 (Unknown) or 0 (Free)
        # We want to show "Covered" areas.
        grid_data = np.zeros((cells_y, cells_x), dtype=np.int8)
        
        # Project 3D -> 2D
        if isinstance(grid_or_sparse, list) or isinstance(grid_or_sparse, set):
            for (gx, gy, gz) in grid_or_sparse:
                if 0 <= gx < cells_x and 0 <= gy < cells_y:
                    # Mark as Occupied/Visited (100)
                    grid_data[gy, gx] = 100
                    
        elif isinstance(grid_or_sparse, np.ndarray) and grid_or_sparse.ndim == 3:
             # Flatten dense
             # Any voxel in Z column means covered?
             projection = np.any(grid_or_sparse, axis=2)
             grid_data[projection] = 100

        msg.data = grid_data.flatten().tolist()
        self.pub_2d_map.publish(msg)

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

    def publish_boundaries(self, x_min, x_max, y_min, y_max, z_min=0.0, z_max=10.0):
        """
        Visualizes the workspace limits as a Line Strip AND Altitude Planes.
        """
        marker_array = MarkerArray()
        
        # 1. Wireframe Box (White)
        marker = Marker()
        marker.header.frame_id = "world"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "boundary_lines"
        marker.id = 0
        marker.type = Marker.LINE_STRIP
        marker.action = Marker.ADD
        marker.scale.x = 0.1 # Thickness
        marker.color = ColorRGBA(r=1.0, g=1.0, b=1.0, a=1.0)
        
        # Ground Loop
        corners = [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max), (x_min, y_min)]
        for x, y in corners: marker.points.append(Point(x=float(x), y=float(y), z=0.0))
        # Ceiling Loop
        for x, y in corners: marker.points.append(Point(x=float(x), y=float(y), z=float(z_max)))
        
        marker_array.markers.append(marker)
        
        # 2. Min Altitude Plane (Red Floor) - "Danger Below"
        if z_min > 0.0:
            plane_min = Marker()
            plane_min.header.frame_id = "world"
            plane_min.header.stamp = self.get_clock().now().to_msg()
            plane_min.ns = "boundary_planes"
            plane_min.id = 1
            plane_min.type = Marker.CUBE
            plane_min.action = Marker.ADD
            
            cx = (x_min + x_max) / 2
            cy = (y_min + y_max) / 2
            
            plane_min.pose.position = Point(x=float(cx), y=float(cy), z=float(z_min))
            plane_min.scale.x = float(x_max - x_min)
            plane_min.scale.y = float(y_max - y_min)
            plane_min.scale.z = 0.05 # Thin sheet
            
            # Semi-transparent Red
            plane_min.color = ColorRGBA(r=1.0, g=0.0, b=0.2, a=0.3)
            marker_array.markers.append(plane_min)

        # 3. Max Altitude Plane (Red Ceiling) - "Danger Above"
        if z_max > 0.0:
            plane_max = Marker()
            plane_max.header.frame_id = "world"
            plane_max.header.stamp = self.get_clock().now().to_msg()
            plane_max.ns = "boundary_planes"
            plane_max.id = 2
            plane_max.type = Marker.CUBE
            plane_max.action = Marker.ADD
            
            cx = (x_min + x_max) / 2
            cy = (y_min + y_max) / 2
            
            plane_max.pose.position = Point(x=float(cx), y=float(cy), z=float(z_max))
            plane_max.scale.x = float(x_max - x_min)
            plane_max.scale.y = float(y_max - y_min)
            plane_max.scale.z = 0.05 
            
            plane_max.color = ColorRGBA(r=1.0, g=0.0, b=0.2, a=0.3)
            marker_array.markers.append(plane_max)

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
