
import numpy as np

class VoxelManager:
    """
    Manages the discretization of the 3D world into Voxels for Volumetric Coverage.
    Approximates an Octomap using a dense 3D numpy grid (efficient for RL scale).
    """
    def __init__(self, x_range=(-20, 20), y_range=(-20, 20), z_range=(0, 10), resolution=1.0):
        self.x_min, self.x_max = x_range
        self.y_min, self.y_max = y_range
        self.z_min, self.z_max = z_range
        self.resolution = resolution
        
        self.dim_x = int((self.x_max - self.x_min) / self.resolution)
        self.dim_y = int((self.y_max - self.y_min) / self.resolution)
        self.dim_z = int((self.z_max - self.z_min) / self.resolution)
        
        # Grid: 0 = Unknown/Unvisited, 1 = Free/Visited
        # In pure coverage tasks, we care about 'Visited'.
        self.grid = np.zeros((self.dim_x, self.dim_y, self.dim_z), dtype=np.int8)
        
        # Metrics
        self.total_voxels = self.dim_x * self.dim_y * self.dim_z
        self.visited_count = 0

    def reset(self):
        self.grid.fill(0)
        self.visited_count = 0
        return self.grid.copy()

    def world_to_voxel(self, x, y, z):
        """Converts world coordinates to voxel indices."""
        gx = int((x - self.x_min) / self.resolution)
        gy = int((y - self.y_min) / self.resolution)
        gz = int((z - self.z_min) / self.resolution)
        return gx, gy, gz

    def update(self, uav_positions: list):
        """
        Updates the voxel grid based on UAV positions.
        Assuming UAV covers the voxel it is currently in (and maybe neighbors).
        
        uav_positions: List of (x, y, z)
        """
        new_visited = 0
        for pos in uav_positions:
            gx, gy, gz = self.world_to_voxel(pos[0], pos[1], pos[2])
            
            # Check bounds
            if (0 <= gx < self.dim_x and 
                0 <= gy < self.dim_y and 
                0 <= gz < self.dim_z):
                
                if self.grid[gx, gy, gz] == 0:
                    self.grid[gx, gy, gz] = 1
                    new_visited += 1
                    self.visited_count += 1
        
        return new_visited

    def merge_from(self, other_manager):
        """
        Merges the knowledge from another VoxelManager into this one.
        Logical OR operation on the grid.
        Returns number of new voxels learned.
        """
        # Find cells that are 0 here but 1 in other
        new_info_mask = (self.grid == 0) & (other_manager.grid == 1)
        new_count = np.sum(new_info_mask)
        
        # Apply Update
        self.grid[new_info_mask] = 1
        self.visited_count += new_count
        
        return new_count

    def get_coverage_ratio(self):
        return self.visited_count / self.total_voxels

    def get_observation(self, x, y, z, r_xy=3, r_z=2):
        """
        Returns a local 3D voxel patch centered around (x,y,z).
        """
        gx, gy, gz = self.world_to_voxel(x, y, z)
        
        # Create a padded version for safe extraction
        # Padding size needs to cover the max radius
        pad_x, pad_y, pad_z = r_xy, r_xy, r_z
        
        # Note: Padding 3D array might be slow every step if grid is huge.
        # Optimized: slicing with boundary checks or pre-padded.
        # For simplicity/readability:
        padded = np.pad(self.grid, ((pad_x, pad_x), (pad_y, pad_y), (pad_z, pad_z)), 
                        mode='constant', constant_values=-1) # -1 for Out of Bounds
        
        # Shift center to padded frame
        cx, cy, cz = gx + pad_x, gy + pad_y, gz + pad_z
        
        patch = padded[cx-r_xy:cx+r_xy+1, 
                       cy-r_xy:cy+r_xy+1, 
                       cz-r_z:cz+r_z+1]
        
        return patch
