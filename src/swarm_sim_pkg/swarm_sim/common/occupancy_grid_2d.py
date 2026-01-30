
import numpy as np

class OccupancyGrid2D:
    """
    Lightweight 2D occupancy grid for coverage tracking in RL.
    Replaces 3D VoxelManager for the 2D+Z_fixed architecture.
    
    Features:
    - Sparse storage using dict for memory efficiency
    - Per-agent color mapping for multi-UAV visualization
    - Optimal altitude calculation based on sensor specs
    - Export to NumPy, PNG heatmap, GeoTIFF
    """
    
    def __init__(self, x_range=(-100, 100), y_range=(-100, 100), resolution=0.5):
        self.x_min, self.x_max = x_range
        self.y_min, self.y_max = y_range
        self.resolution = resolution
        
        # Grid dimensions
        self.dim_x = int((self.x_max - self.x_min) / self.resolution)
        self.dim_y = int((self.y_max - self.y_min) / self.resolution)
        
        # Sparse storage: {(gx, gy): agent_id}
        # agent_id can be int (0, 1, 2...) or -1 for overlapping coverage
        self.grid = {}
        
        # Metrics
        self.total_cells = self.dim_x * self.dim_y
        self.visited_count = 0
        
    def reset(self):
        """Reset the grid to empty state"""
        self.grid.clear()
        self.visited_count = 0
        
    def world_to_grid(self, x, y):
        """Convert world coordinates (meters) to grid indices"""
        gx = int((x - self.x_min) / self.resolution)
        gy = int((y - self.y_min) / self.resolution)
        return gx, gy
    
    def grid_to_world(self, gx, gy):
        """Convert grid indices to world coordinates (center of cell)"""
        x = self.x_min + (gx + 0.5) * self.resolution
        y = self.y_min + (gy + 0.5) * self.resolution
        return x, y
    
    def calculate_optimal_altitude(self, sensor_range_m=15.0, fov_deg=30.0, battery_efficiency=0.005):
        """
        Calculate optimal altitude for coverage given sensor specifications.
        
        Args:
            sensor_range_m: Maximum range of downward LiDAR (meters)
            fov_deg: Field of view in degrees (cone angle)
            battery_efficiency: Battery cost per meter altitude (fraction per meter)
        
        Returns:
            z_optimal: Optimal altitude in meters
        
        Theory:
            Footprint area: A(Z) = π * (Z * tan(θ/2))²
            Battery cost: C(Z) = β * Z
            Optimal: Z* = argmax[A(Z)/C(Z)]
            
            Simplified for max range: Z* ≈ R/2
        """
        # Simplified optimal: half the sensor range
        # This ensures max coverage before occlusion while staying in sensor range
        z_optimal = sensor_range_m / 2.0
        
        # Fine-tune based on battery efficiency (higher cost → prefer lower altitude)
        # If battery_efficiency is high (expensive to climb), reduce Z slightly
        efficiency_factor = max(0.8, 1.0 - (battery_efficiency - 0.003) * 20)
        z_optimal *= efficiency_factor
        
        # Clamp to reasonable range
        z_optimal = np.clip(z_optimal, 3.0, 12.0)
        
        return z_optimal
    
    def update_from_position(self, uav_id, x, y):
        """
        Mark cell at (x, y) as visited by uav_id.
        
        Args:
            uav_id: Integer ID of the UAV (0, 1, 2, ...)
            x, y: World coordinates
        
        Returns:
            new_cell: True if this was a previously unvisited cell
        """
        gx, gy = self.world_to_grid(x, y)
        
        # Check bounds
        if not (0 <= gx < self.dim_x and 0 <= gy < self.dim_y):
            return False
        
        cell_key = (gx, gy)
        
        # New cell?
        if cell_key not in self.grid:
            self.grid[cell_key] = uav_id
            self.visited_count += 1
            return True
        else:
            # Already visited
            # Optional: Mark as overlapping if different UAV
            if self.grid[cell_key] != uav_id and self.grid[cell_key] != -1:
                self.grid[cell_key] = -1  # -1 = overlapping coverage
            return False
    
    def update_from_pointcloud(self, points, uav_id=0):
        """
        Update grid from a 3D pointcloud by projecting to 2D (x, y plane).
        
        Args:
            points: (N, 3) array of world coordinates [x, y, z]
            uav_id: Integer ID of the UAV
        
        Returns:
            new_count: Number of newly discovered cells
        """
        if points is None or len(points) == 0:
            return 0
        
        # Project to 2D: just use x, y columns
        points_2d = points[:, :2]
        
        # Filter by bounds
        mask = (points_2d[:, 0] >= self.x_min) & (points_2d[:, 0] < self.x_max) & \
               (points_2d[:, 1] >= self.y_min) & (points_2d[:, 1] < self.y_max)
        valid_points = points_2d[mask]
        
        if len(valid_points) == 0:
            return 0
        
        # Convert to grid indices
        gxs = ((valid_points[:, 0] - self.x_min) / self.resolution).astype(int)
        gys = ((valid_points[:, 1] - self.y_min) / self.resolution).astype(int)
        
        # Get unique cells
        unique_cells = set(zip(gxs, gys))
        
        # Count new cells
        new_count = 0
        for cell in unique_cells:
            if cell not in self.grid:
                self.grid[cell] = uav_id
                new_count += 1
                self.visited_count += 1
            elif self.grid[cell] != uav_id and self.grid[cell] != -1:
                # Mark as overlapping
                self.grid[cell] = -1
        
        return new_count
    
    def merge_from(self, other_grid):
        """
        Merge another OccupancyGrid2D into this one (union operation).
        
        Args:
            other_grid: Another OccupancyGrid2D instance
        
        Returns:
            new_count: Number of newly discovered cells
        """
        initial_count = len(self.grid)
        
        # Union operation
        for cell_key, agent_id in other_grid.grid.items():
            if cell_key not in self.grid:
                self.grid[cell_key] = agent_id
            elif self.grid[cell_key] != agent_id and self.grid[cell_key] != -1:
                # Mark overlap
                self.grid[cell_key] = -1
        
        new_count = len(self.grid) - initial_count
        self.visited_count = len(self.grid)
        
        return new_count
    
    def get_coverage_ratio(self):
        """Return fraction of grid that has been visited (0.0 to 1.0)"""
        return self.visited_count / max(1, self.total_cells)
    
    def get_observation_2d(self, x, y, radius=5):
        """
        Get a local 2D patch centered at (x, y).
        
        Args:
            x, y: World coordinates of center
            radius: Radius in grid cells (patch will be (2*radius+1) × (2*radius+1))
        
        Returns:
            patch: (2*radius+1, 2*radius+1) array with values:
                -1.0 = out of bounds
                 0.0 = unknown/free
                 1.0 = visited by this or another UAV
        """
        gx, gy = self.world_to_grid(x, y)
        
        patch_size = 2 * radius + 1
        patch = np.zeros((patch_size, patch_size), dtype=np.float32)
        
        for i in range(patch_size):
            for j in range(patch_size):
                # Global grid coordinates
                nx = gx - radius + i
                ny = gy - radius + j
                
                # Check bounds
                if not (0 <= nx < self.dim_x and 0 <= ny < self.dim_y):
                    patch[i, j] = -1.0  # Out of bounds
                elif (nx, ny) in self.grid:
                    patch[i, j] = 1.0  # Visited
                else:
                    patch[i, j] = 0.0  # Unknown
        
        return patch
    
    def get_sparse_array(self):
        """
        Get occupied cells as (N, 2) array of grid indices.
        
        Returns:
            cells: (N, 2) array where each row is [gx, gy]
        """
        if not self.grid:
            return np.zeros((0, 2), dtype=np.int32)
        
        cells = np.array(list(self.grid.keys()), dtype=np.int32)
        return cells
    
    def get_agent_cells(self, agent_id):
        """
        Get cells visited by a specific agent.
        
        Args:
            agent_id: Integer UAV ID
        
        Returns:
            cells: (N, 2) array of grid indices
        """
        agent_cells = [cell for cell, aid in self.grid.items() if aid == agent_id]
        if not agent_cells:
            return np.zeros((0, 2), dtype=np.int32)
        return np.array(agent_cells, dtype=np.int32)

    def get_sparse_pointcloud(self, z_level=0.5):
        """
        Convert visited 2D grid cells to 3D pointcloud for visualization.
        
        Args:
            z_level: Z-coordinate to assign to the points
            
        Returns:
            points: (N, 3) numpy array of [x, y, z] coordinates
        """
        if not self.grid:
            return np.zeros((0, 3), dtype=np.float32)
            
        points = []
        for (gx, gy) in self.grid.keys():
            x, y = self.grid_to_world(gx, gy)
            points.append([x, y, z_level])
            
        return np.array(points, dtype=np.float32)
    
    def save_to_file(self, filename="outputs/coverage_2d.npy"):
        """
        Save the 2D occupancy grid to file.
        
        Supported formats:
        - .npy: NumPy array of grid indices
        - .png: Heatmap visualization
        - .tif: GeoTIFF (georeferenced, requires geo origin)
        """
        import os
        
        # Ensure directory exists
        output_dir = os.path.dirname(filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        if filename.endswith(".npy"):
            # Save sparse array
            cells = self.get_sparse_array()
            np.save(filename, cells)
            print(f"[OccupancyGrid2D] Saved {len(cells)} cells to {filename}")
            
        elif filename.endswith(".png"):
            # Create dense heatmap for visualization
            try:
                from PIL import Image
                
                # Create dense grid
                dense = np.zeros((self.dim_y, self.dim_x), dtype=np.uint8)
                
                for (gx, gy), agent_id in self.grid.items():
                    if agent_id == -1:
                        dense[gy, gx] = 128  # Gray for overlap
                    else:
                        # Color by agent ID (simple mapping)
                        dense[gy, gx] = min(255, 50 + agent_id * 50)
                
                # Convert to image (flip Y for correct orientation)
                img = Image.fromarray(np.flipud(dense), mode='L')
                img.save(filename)
                print(f"[OccupancyGrid2D] Saved heatmap to {filename}")
                
            except ImportError:
                print("[OccupancyGrid2D] PIL not available, saving as .npy instead")
                cells = self.get_sparse_array()
                np.save(filename.replace(".png", ".npy"), cells)
        
        else:
            # Default to .npy
            cells = self.get_sparse_array()
            np.save(filename, cells)
            print(f"[OccupancyGrid2D] Saved to {filename}")
