
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
        
        # Dimensions are theoretical max, but we won't allocate a grid this big anymore.
        self.dim_x = int((self.x_max - self.x_min) / self.resolution)
        self.dim_y = int((self.y_max - self.y_min) / self.resolution)
        self.dim_z = int((self.z_max - self.z_min) / self.resolution)
        
        # Sparse Grid: set of (gx, gy, gz) tuples
        # 0 = Unknown (Implicit), 1 = Occupied/Visited (In Set)
        self.sparse_grid = set() 
        
        # Metrics
        self.total_voxels = self.dim_x * self.dim_y * self.dim_z # Theoretical max
        self.visited_count = 0

    def reset(self):
        self.sparse_grid.clear()
        self.visited_count = 0

    def world_to_voxel(self, x, y, z):
        """Converts world coordinates to voxel indices."""
        gx = int((x - self.x_min) / self.resolution)
        gy = int((y - self.y_min) / self.resolution)
        gz = int((z - self.z_min) / self.resolution)
        return gx, gy, gz

    def update(self, uav_positions: list):
        """
        Updates the voxel grid based on UAV positions.
        """
        new_visited = 0
        for pos in uav_positions:
            gx, gy, gz = self.world_to_voxel(pos[0], pos[1], pos[2])
            
            # Check bounds (optional for sparse, but good for keeping "Map Limits")
            if (0 <= gx < self.dim_x and 
                0 <= gy < self.dim_y and 
                0 <= gz < self.dim_z):
                
                voxel_key = (gx, gy, gz)
                if voxel_key not in self.sparse_grid:
                    self.sparse_grid.add(voxel_key)
                    new_visited += 1
                    self.visited_count += 1
        
        return new_visited

    def update_from_pointcloud(self, points: np.ndarray):
        """
        Updates grid based on a list of hits (occupied voxels).
        points: (N, 3) array of world coordinates.
        """
        if points is None or len(points) == 0:
            return 0
            
        new_visited = 0
        
        # Vectorized lookup is hard with sparse set, loop is fine for N < 10000
        # Optimization: Filter bounds first
        mask = (points[:,0] >= self.x_min) & (points[:,0] < self.x_max) & \
               (points[:,1] >= self.y_min) & (points[:,1] < self.y_max) & \
               (points[:,2] >= self.z_min) & (points[:,2] < self.z_max)
        valid_points = points[mask]
        
        # Convert to voxels
        # (p - min) / res
        gxs = ((valid_points[:, 0] - self.x_min) / self.resolution).astype(int)
        gys = ((valid_points[:, 1] - self.y_min) / self.resolution).astype(int)
        gzs = ((valid_points[:, 2] - self.z_min) / self.resolution).astype(int)
        
        # Combine to tuples
        # Using a set update is faster than checking one by one
        # But we need to count NEW ones.
        
        # Unique voxels in this scan
        keys = set(zip(gxs, gys, gzs))
        
        # Check against existing
        # This is where 0 vs 1 matters.
        # User wants "Occupancy". 
        # In our simplified logic: If Lidar Hits -> It is Occupied (1).
        # We assume 1 is the state we store.
        
        new_keys = keys - self.sparse_grid
        
        if new_keys:
            self.sparse_grid.update(new_keys)
            count = len(new_keys)
            self.visited_count += count
            new_visited = count
            
        return new_visited

    def merge_from(self, other_manager):
        """
        Merges sparse grids. Union operation.
        """
        initial_len = len(self.sparse_grid)
        self.sparse_grid.update(other_manager.sparse_grid)
        final_len = len(self.sparse_grid)
        
        new_count = final_len - initial_len
        self.visited_count = final_len
        return new_count

    def get_coverage_ratio(self):
        return self.visited_count / self.total_voxels

    def get_observation(self, x, y, z, r_xy=3, r_z=2):
        """
        Returns a local 3D voxel patch (DENSE) centered around (x,y,z).
        We construct the dense patch on the fly from the sparse set.
        """
        gx, gy, gz = self.world_to_voxel(x, y, z)
        
        dim_x = 2 * r_xy + 1
        dim_y = 2 * r_xy + 1
        dim_z = 2 * r_z + 1
        
        # Local dense patch for CNN
        patch = np.zeros((dim_x, dim_y, dim_z), dtype=np.float32)
        
        # Iterate over the theoretical patch volume
        # (Optimization: could iterate over relevant sparse keys, but usually patch is small enough)
        for i in range(dim_x):
            for j in range(dim_y):
                for k in range(dim_z):
                    # Global coords of this patch cell
                    nx = gx - r_xy + i
                    ny = gy - r_xy + j
                    nz = gz - r_z + k
                    
                    # Check Out of Bounds
                    if not (0 <= nx < self.dim_x and 0 <= ny < self.dim_y and 0 <= nz < self.dim_z):
                        patch[i, j, k] = -1.0 # Out of bounds
                    elif (nx, ny, nz) in self.sparse_grid:
                        patch[i, j, k] = 1.0 # Occupied/Visited
                    else:
                        patch[i, j, k] = 0.0 # Free/Unknown
        
        return patch

    def get_sparse_pointcloud(self):
        """Returns the occupied voxels as a (N, 3) numpy array."""
        if not self.sparse_grid:
            return np.zeros((0, 3), dtype=np.int32)
        return np.array(list(self.sparse_grid), dtype=np.int32)
