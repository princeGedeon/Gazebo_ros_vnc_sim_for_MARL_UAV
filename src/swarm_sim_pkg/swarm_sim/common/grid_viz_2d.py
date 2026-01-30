#!/usr/bin/env python3
"""
2D Grid Visualizer for RViz
Publishes OccupancyGrid and GridCells for per-agent coverage visualization
"""

import numpy as np
import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
from nav_msgs.msg import GridCells
from geometry_msgs.msg import Point
from std_msgs.msg import Header


class Grid2DVisualizer:
    """
    Publishes 2D coverage grids to RViz.
    
    Topics:
    - /coverage/global_map (OccupancyGrid): Full coverage map
    - /coverage/uav_X (GridCells): Per-agent colored cells
    """
    
    def __init__(self, node, occupancy_grid_2d, frame_id='map'):
        self.node = node
        self.grid = occupancy_grid_2d
        self.frame_id = frame_id
        
        # Publisher: Global coverage as OccupancyGrid
        self.global_pub = self.node.create_publisher(
            OccupancyGrid, 
            '/coverage/global_map', 
            10
        )
        
        # Publishers: Per-agent coverage as GridCells
        self.agent_pubs = {}
        
    def register_agent(self, agent_id):
        """Register a UAV for per-agent visualization"""
        topic = f'/coverage/uav_{agent_id}'
        pub = self.node.create_publisher(GridCells, topic, 10)
        self.agent_pubs[agent_id] = pub
    
    def publish_global_map(self):
        """
        Publish global coverage map as OccupancyGrid.
        
        Values:
        - -1 (unknown): Gray
        -  0 (free): White
        - 100 (visited): Black
        """
        msg = OccupancyGrid()
        
        # Header
        msg.header = Header()
        msg.header.stamp = self.node.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        
        # Map metadata
        msg.info.resolution = self.grid.resolution
        msg.info.width = self.grid.dim_x
        msg.info.height = self.grid.dim_y
        msg.info.origin.position.x = self.grid.x_min
        msg.info.origin.position.y = self.grid.y_min
        msg.info.origin.position.z = 0.0
        msg.info.origin.orientation.w = 1.0
        
        # Create dense grid (inefficient but standard for RViz)
        # -1 = unknown, 0 = free, 100 = occupied/visited
        data = np.full(self.grid.dim_x * self.grid.dim_y, -1, dtype=np.int8)
        
        # Mark visited cells as 100 (black in RViz)
        for (gx, gy) in self.grid.grid.keys():
            idx = gy * self.grid.dim_x + gx
            if idx < len(data):
                data[idx] = 100
        
        msg.data = data.tolist()
        
        self.global_pub.publish(msg)
    
    def publish_agent_cells(self, agent_id):
        """
        Publish cells visited by a specific agent as GridCells.
        Displayed as colored cubes in RViz.
        """
        if agent_id not in self.agent_pubs:
            self.register_agent(agent_id)
        
        # Get cells visited by this agent
        cells_idx = self.grid.get_agent_cells(agent_id)
        
        if len(cells_idx) == 0:
            return
        
        msg = GridCells()
        msg.header = Header()
        msg.header.stamp = self.node.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        
        msg.cell_width = self.grid.resolution
        msg.cell_height = self.grid.resolution
        
        # Convert grid indices to world coordinates
        points = []
        for gx, gy in cells_idx:
            x, y = self.grid.grid_to_world(gx, gy)
            p = Point()
            p.x = x
            p.y = y
            p.z = 0.1  # Slight elevation for visibility
            points.append(p)
        
        msg.cells = points
        
        self.agent_pubs[agent_id].publish(msg)
    
    def publish_all_agents(self, num_agents):
        """Publish GridCells for all agents"""
        for i in range(num_agents):
            self.publish_agent_cells(i)
